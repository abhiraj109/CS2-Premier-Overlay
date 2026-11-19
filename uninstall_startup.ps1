$ErrorActionPreference = 'Stop'
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$shortcutPaths = @('Roundframe for CS2.lnk', 'CS2 Premier Sync Overlay.lnk') | ForEach-Object { Join-Path $startup $_ }
$removed = $false
foreach ($shortcutPath in $shortcutPaths) {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force
        $removed = $true
    }
}
if ($removed) {
    Write-Host 'Startup shortcut removed.' -ForegroundColor Green
} else {
    Write-Host 'No startup shortcut was installed.' -ForegroundColor Yellow
}
