# Optional bundled Ollama installer

Place the official Windows Ollama installer here as:

```text
packaging/vendor/OllamaSetup.exe
```

When this file exists:

- PyInstaller includes it beside `StudyVaultAI.exe`.
- The Inno Setup installer can run it during installation if `ollama` is not already available.
- The app's first-run setup prefers this bundled installer before downloading from the web.

If the file is absent, StudyVault still works: first-run setup downloads the official installer when needed.

