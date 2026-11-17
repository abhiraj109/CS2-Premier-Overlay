$ErrorActionPreference = 'Stop'
$shortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\CS2 Premier Sync Overlay.lnk'
if (Test-Path $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
    Write-Host 'Startup shortcut removed.' -ForegroundColor Green
} else {
    Write-Host 'No startup shortcut was installed.' -ForegroundColor Yellow
}
