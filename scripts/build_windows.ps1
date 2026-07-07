param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "BRender Windows build" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m PyInstaller --clean --noconfirm BRender.spec

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable: dist\\BRender.exe" -ForegroundColor Green
