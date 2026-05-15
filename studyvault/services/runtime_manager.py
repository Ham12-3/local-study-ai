from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from studyvault.services.local_data import APP_DATA_DIR
from studyvault.services.ollama import OllamaClient


OLLAMA_WINDOWS_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
RECOMMENDED_MODEL = os.environ.get("STUDYVAULT_RECOMMENDED_MODEL", "llama3.2:1b")


@dataclass(frozen=True)
class RuntimeState:
    installed: bool
    running: bool
    models: list[str]
    executable: str | None = None
    platform_name: str = platform.system()
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.installed and self.running and bool(self.models)


class RuntimeManager:
    """Detects, starts, and bootstraps the local Ollama runtime."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()
        self._serve_process: subprocess.Popen | None = None

    def inspect(self) -> RuntimeState:
        executable = self.find_ollama_executable()
        status = self.client.list_models(timeout=1.5)
        return RuntimeState(
            installed=bool(executable),
            running=status.running,
            models=status.models,
            executable=executable,
            error=status.error,
        )

    def find_ollama_executable(self) -> str | None:
        found = shutil.which("ollama")
        if found:
            return found

        candidates: list[Path] = []
        if platform.system() == "Windows":
            local_app_data = os.environ.get("LOCALAPPDATA")
            program_files = os.environ.get("ProgramFiles")
            if local_app_data:
                candidates.append(Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe")
            if program_files:
                candidates.append(Path(program_files) / "Ollama" / "ollama.exe")
            candidates.append(Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe")
        else:
            candidates.extend([Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama")])

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def download_windows_installer(
        self,
        progress: Callable[[int], None] | None = None,
        status: Callable[[str], None] | None = None,
    ) -> Path:
        bundled = self.find_bundled_windows_installer()
        if bundled:
            if status:
                status("Using bundled Ollama installer")
            if progress:
                progress(100)
            return bundled

        installer_dir = APP_DATA_DIR / "installers"
        installer_dir.mkdir(parents=True, exist_ok=True)
        target = installer_dir / "OllamaSetup.exe"
        partial = installer_dir / "OllamaSetup.exe.part"

        if target.exists() and target.stat().st_size > 1_000_000:
            if status:
                status("Using cached Ollama installer")
            if progress:
                progress(100)
            return target
        if target.exists():
            target.unlink()
        if partial.exists():
            partial.unlink()

        request = urllib.request.Request(
            OLLAMA_WINDOWS_INSTALLER_URL,
            headers={"User-Agent": "StudyVaultAI/0.1"},
        )
        if status:
            status("Connecting to official Ollama download")

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                last_status_at = 0
                last_byte_at = time.monotonic()
                with partial.open("wb") as file:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        file.write(chunk)
                        downloaded += len(chunk)
                        last_byte_at = time.monotonic()
                        if progress and total:
                            progress(min(99, int(downloaded * 100 / total)))
                        if status and downloaded - last_status_at >= 2_000_000:
                            last_status_at = downloaded
                            if total:
                                status(f"Downloading Ollama installer ({downloaded // 1_000_000} MB of {total // 1_000_000} MB)")
                            else:
                                status(f"Downloading Ollama installer ({downloaded // 1_000_000} MB)")
                        if time.monotonic() - last_byte_at > 30:
                            raise TimeoutError("Ollama installer download stalled.")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if partial.exists():
                partial.unlink()
            raise RuntimeError(f"Could not download Ollama installer: {exc}") from exc

        if partial.stat().st_size < 1_000_000:
            partial.unlink()
            raise RuntimeError("The Ollama installer download was empty or incomplete.")
        partial.replace(target)
        if progress:
            progress(100)
        if status:
            status("Ollama installer downloaded")
        return target

    def find_bundled_windows_installer(self) -> Path | None:
        candidates: list[Path] = []
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            candidates.append(Path(bundle_dir) / "OllamaSetup.exe")
            candidates.append(Path(bundle_dir) / "vendor" / "OllamaSetup.exe")
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).resolve().parent / "OllamaSetup.exe")
            candidates.append(Path(sys.executable).resolve().parent / "vendor" / "OllamaSetup.exe")
        candidates.append(Path.cwd() / "packaging" / "vendor" / "OllamaSetup.exe")

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def run_windows_installer(self, installer: Path) -> None:
        # The installer is intentionally visible: Windows may need a UAC prompt
        # or user confirmation, and hiding that window makes setup feel stuck.
        process = subprocess.Popen([str(installer)])
        process.wait()

    def install_ollama(
        self,
        progress: Callable[[int], None] | None = None,
        status: Callable[[str], None] | None = None,
    ) -> RuntimeState:
        if platform.system() != "Windows":
            raise RuntimeError("Automatic Ollama installation is currently implemented for Windows.")
        installer = self.download_windows_installer(progress, status)
        if not installer.exists() or installer.stat().st_size < 1_000_000:
            raise RuntimeError("The cached Ollama installer is missing or incomplete.")
        if status:
            status("Opening Ollama installer")
        self.run_windows_installer(installer)
        if status:
            status("Waiting for Ollama installation to finish")
        state = self.wait_for_install()
        if not state.installed:
            raise RuntimeError(
                "Ollama installer closed, but ollama.exe was not found. "
                "Finish the installer window, then choose Check again."
            )
        return state

    def wait_for_install(self, timeout_seconds: int = 90) -> RuntimeState:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            state = self.inspect()
            if state.installed:
                return state
            time.sleep(2)
        return self.inspect()

    def start_ollama(self) -> RuntimeState:
        state = self.inspect()
        if state.running:
            return state
        if not state.executable:
            raise RuntimeError("Ollama is not installed.")

        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._serve_process = subprocess.Popen(
            [state.executable, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        return self.wait_until_running()

    def wait_until_running(self, timeout_seconds: int = 45) -> RuntimeState:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            state = self.inspect()
            if state.running:
                return state
            time.sleep(1)
        return self.inspect()

    def pull_model(
        self,
        model: str = RECOMMENDED_MODEL,
        progress: Callable[[int], None] | None = None,
        status: Callable[[str], None] | None = None,
    ) -> RuntimeState:
        executable = self.find_ollama_executable()
        if not executable:
            raise RuntimeError("Ollama is not installed.")
        self.start_ollama()
        if status:
            status("Downloading recommended study model")
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            [executable, "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )
        last_progress = 5
        if progress:
            progress(last_progress)
        assert process.stdout is not None
        for line in process.stdout:
            clean = line.strip()
            if status and clean:
                status(clean)
            percent = self._extract_percent(clean)
            if percent is not None:
                last_progress = max(last_progress, percent)
                if progress:
                    progress(last_progress)
        code = process.wait()
        if code != 0:
            raise RuntimeError(f"Model download failed with exit code {code}.")
        if progress:
            progress(100)
        return self.inspect()

    def auto_setup(
        self,
        progress: Callable[[int], None] | None = None,
        status: Callable[[str], None] | None = None,
    ) -> RuntimeState:
        state = self.inspect()
        if state.ready:
            if status:
                status("Local AI is ready")
            if progress:
                progress(100)
            return state

        if not state.installed:
            if status:
                status("Installing local AI runtime")
            state = self.install_ollama(progress, status)

        if not state.running:
            if status:
                status("Starting local AI service")
            state = self.start_ollama()
            if progress:
                progress(35)

        if not state.models:
            if status:
                status("Preparing fast study model")
            state = self.pull_model(RECOMMENDED_MODEL, progress, status)

        if progress:
            progress(100)
        return state

    @staticmethod
    def _extract_percent(text: str) -> int | None:
        marker = "%"
        if marker not in text:
            return None
        before = text.split(marker, 1)[0]
        digits = ""
        for char in reversed(before):
            if char.isdigit():
                digits = char + digits
            elif digits:
                break
        if not digits:
            return None
        return max(0, min(100, int(digits)))
