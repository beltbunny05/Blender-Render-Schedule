param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "dist\BRender.exe")) {
    throw "dist\BRender.exe not found. Run scripts\build_windows.ps1 first."
}

$releaseDir = "dist\BRender-Windows"
$zipPath = "dist\BRender-Windows-$Version.zip"

if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}

New-Item -ItemType Directory -Path $releaseDir | Out-Null
Copy-Item "dist\BRender.exe" "$releaseDir\BRender.exe"
Copy-Item "README.md" "$releaseDir\README.md"

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path "$releaseDir\*" -DestinationPath $zipPath

Write-Host ""
Write-Host "Release package created:" -ForegroundColor Green
Write-Host $zipPath -ForegroundColor Green
