# Windows packaging

StudyVault AI uses two packaging layers:

1. PyInstaller builds the desktop app folder:

   ```powershell
   .\packaging\build_windows.ps1 -SkipInstaller
   ```

   Output:

   ```text
   dist\StudyVaultAI\StudyVaultAI.exe
   ```

2. Inno Setup turns that folder into a user-friendly Windows installer:

   ```powershell
   .\packaging\build_windows.ps1
   ```

   Output:

   ```text
   dist\installer\StudyVaultAI-Setup.exe
   ```

## Bundling Ollama

To make the app setup handle local AI without sending users to another website, download the official Ollama installer before building:

```powershell
.\packaging\build_windows.ps1 -BundleOllama
```

This saves:

```text
packaging\vendor\OllamaSetup.exe
```

When present, it is included in the PyInstaller output and the Inno Setup installer. StudyVault also prefers this bundled installer during first-run auto setup.

If the installer is not bundled, StudyVault still downloads the official Ollama installer during first-run setup.

## Requirements

- Windows
- Python with dependencies from `requirements.txt`
- PyInstaller from `requirements-dev.txt`
- Inno Setup 6 for the final installer

For smoke tests that should not install Ollama or download a model:

```powershell
$env:STUDYVAULT_DISABLE_AUTO_SETUP="1"
.\dist\StudyVaultAI\StudyVaultAI.exe
```

