param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "BRender Windows build" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

if (-not (Test-Path $python)) {
    throw ".venv\\Scripts\\python.exe not found. Create the virtual environment first with: python -m venv .venv"
}

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements-dev.txt
& $python -m PyInstaller --clean --noconfirm BRender.spec

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable: dist\\BRender.exe" -ForegroundColor Green
