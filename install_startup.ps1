$ErrorActionPreference = 'Stop'
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
New-Item -ItemType Directory -Force -Path $startup | Out-Null
$shortcutPath = Join-Path $startup 'CS2 Premier Sync Overlay.lnk'
$target = Join-Path $PSScriptRoot 'run_overlay.bat'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.WindowStyle = 7
$shortcut.Description = 'Starts the local CS2 Premier OBS overlay at Windows sign-in.'
$shortcut.Save()
Write-Host 'Startup shortcut installed. The overlay will launch minimized at next Windows sign-in.' -ForegroundColor Green
Write-Host $shortcutPath -ForegroundColor Cyan
