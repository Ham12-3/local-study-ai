# StudyVault AI

A local-first PySide6 desktop study app with a premium dark UI shell, reusable design system, and guided local AI setup.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m studyvault
```

## Local AI setup

On first launch, StudyVault automatically prepares local AI:

- If Ollama is missing, the app downloads and opens the official Windows installer.
- If Ollama is installed but stopped, the app starts it in the background.
- If Ollama is running but has no models, the app pulls a fast starter study model.
- Settings still populate model dropdowns dynamically from `http://127.0.0.1:11434/api/tags`.

For packaging, the setup model can be changed without editing UI code:

```powershell
$env:STUDYVAULT_RECOMMENDED_MODEL="your-model-name"
python -m studyvault
```

Developers can prevent automatic install/download attempts during smoke tests:

```powershell
$env:STUDYVAULT_DISABLE_AUTO_SETUP="1"
python -m studyvault
```

No textbook subjects, remote fonts, remote icons, images, or web UI assets are bundled into the desktop frontend.

## Package for Windows

Build the desktop executable folder:

```powershell
.\packaging\build_windows.ps1 -SkipInstaller
```

Build a full installer with bundled Ollama setup support:

```powershell
.\packaging\build_windows.ps1 -BundleOllama
```

The final installer requires Inno Setup 6. Packaging details live in `packaging/README.md`.
