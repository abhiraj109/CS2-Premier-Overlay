$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
foreach ($script in Get-ChildItem -LiteralPath $root -Filter '*.ps1') {
    $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($script.FullName, [ref]$null, [ref]$parseErrors)
    if ($parseErrors) { throw ($parseErrors -join [Environment]::NewLine) }
}

$scratch = Join-Path ([IO.Path]::GetTempPath()) ('Overlay Test ' + [guid]::NewGuid())
$steam = Join-Path $scratch 'Steam'
$library = Join-Path $scratch 'Other Steam Library'
$gameCfg = Join-Path $library 'steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg'
$config = 'gamestate_integration_cs2_obs_overlay.cfg'
$previousAppData = $env:APPDATA

function Get-ItemProperty {
    param([string]$Path)
    if ($Path -eq 'HKCU:\Software\Valve\Steam') { return @{ SteamPath = $steam } }
    throw 'Fixture registry entry missing'
}

try {
    $null = New-Item -ItemType Directory -Path (Join-Path $steam 'steamapps'), $gameCfg -Force
    $escaped = $library.Replace('\', '\\')
    Set-Content -LiteralPath (Join-Path $steam 'steamapps\libraryfolders.vdf') -Value ('"path" "' + $escaped + '"')
    & (Join-Path $root 'install_gsi.ps1')
    $installed = Join-Path $gameCfg $config
    if ((Get-FileHash $installed).Hash -ne (Get-FileHash (Join-Path $root "gsi\$config")).Hash) {
        throw 'GSI file mismatch'
    }
    & (Join-Path $root 'uninstall_gsi.ps1')
    & (Join-Path $root 'uninstall_gsi.ps1')
    if (Test-Path -LiteralPath $installed) { throw 'GSI file still present' }

    $env:APPDATA = Join-Path $scratch 'AppData'
    & (Join-Path $root 'install_startup.ps1')
    $link = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\CS2 Premier Sync Overlay.lnk'
    $shell = New-Object -ComObject WScript.Shell
    if (!(Test-Path -LiteralPath $link) -or
        $shell.CreateShortcut($link).TargetPath -ne (Join-Path $root 'run_overlay.bat')) {
        throw 'Startup shortcut target mismatch'
    }
    & (Join-Path $root 'uninstall_startup.ps1')
    & (Join-Path $root 'uninstall_startup.ps1')
    if (Test-Path -LiteralPath $link) { throw 'Startup shortcut still present' }
    Write-Host 'PowerShell syntax, GSI and Startup fixture checks passed.'
} finally {
    $env:APPDATA = $previousAppData
    $resolved = Resolve-Path -LiteralPath $scratch -ErrorAction SilentlyContinue
    if ($resolved -and $resolved.Path -eq $scratch) { Remove-Item -LiteralPath $resolved.Path -Recurse -Force }
}
