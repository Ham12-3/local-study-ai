param(
    [switch]$Clean,
    [switch]$BundleOllama,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Get-Process StudyVaultAI -ErrorAction SilentlyContinue | Stop-Process -Force

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue `
        (Join-Path $Root "build"),
        (Join-Path $Root "dist")
}

if ($BundleOllama) {
    & (Join-Path $PSScriptRoot "fetch_ollama_installer.ps1")
}

python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Failed to install runtime requirements." }
python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Failed to install packaging requirements." }
python -m PyInstaller packaging\studyvault.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$Exe = Join-Path $Root "dist\StudyVaultAI\StudyVaultAI.exe"
if (-not (Test-Path $Exe)) {
    throw "PyInstaller did not create $Exe"
}

Write-Host "Built desktop app:" $Exe

if (-not $SkipInstaller) {
    $InnoCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $ISCC = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($ISCC) {
        & $ISCC (Join-Path $Root "packaging\StudyVaultAI.iss")
    }
    else {
        Write-Host "Inno Setup 6 was not found. Install it to build the Windows installer."
        Write-Host "The unpacked app is still ready in dist\StudyVaultAI."
    }
}
