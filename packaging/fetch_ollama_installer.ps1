$ErrorActionPreference = "Stop"

$Vendor = Join-Path $PSScriptRoot "vendor"
$Target = Join-Path $Vendor "OllamaSetup.exe"
$Url = "https://ollama.com/download/OllamaSetup.exe"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null
Write-Host "Downloading official Ollama installer..."
Write-Host $Url
Invoke-WebRequest -Uri $Url -OutFile $Target
Write-Host "Saved:" $Target

