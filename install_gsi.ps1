$ErrorActionPreference = 'Stop'
$ConfigSource = Join-Path $PSScriptRoot 'gsi\gamestate_integration_cs2_obs_overlay.cfg'
if (-not (Test-Path $ConfigSource)) {
    Write-Host "GSI config not found: $ConfigSource" -ForegroundColor Red
    exit 1
}

$steamRoots = New-Object System.Collections.Generic.List[string]
$registryPaths = @(
    'HKCU:\Software\Valve\Steam',
    'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam',
    'HKLM:\SOFTWARE\Valve\Steam'
)
foreach ($key in $registryPaths) {
    try {
        $item = Get-ItemProperty -Path $key -ErrorAction Stop
        foreach ($property in @('SteamPath', 'InstallPath')) {
            $value = $item.$property
            if ($value -and (Test-Path $value)) { $steamRoots.Add((Resolve-Path $value).Path) }
        }
    } catch { }
}

$libraryRoots = New-Object System.Collections.Generic.List[string]
foreach ($root in $steamRoots) {
    if (-not $libraryRoots.Contains($root)) { $libraryRoots.Add($root) }
    $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
    if (Test-Path $vdf) {
        $content = Get-Content $vdf -Raw
        foreach ($match in [regex]::Matches($content, '"path"\s+"([^"]+)"')) {
            $lib = $match.Groups[1].Value -replace '\\\\', '\'
            if ($lib -and (Test-Path $lib) -and -not $libraryRoots.Contains($lib)) { $libraryRoots.Add($lib) }
        }
    }
}

$found = $null
foreach ($lib in $libraryRoots) {
    $candidate = Join-Path $lib 'steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg'
    if (Test-Path $candidate) { $found = $candidate; break }
}

if (-not $found) {
    Write-Host 'Could not automatically find the CS2 cfg folder.' -ForegroundColor Yellow
    Write-Host 'Find your CS2 install and copy the config into:'
    Write-Host '...\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\' -ForegroundColor Cyan
    exit 2
}

New-Item -ItemType Directory -Force -Path $found | Out-Null
$destination = Join-Path $found 'gamestate_integration_cs2_obs_overlay.cfg'
Copy-Item -Path $ConfigSource -Destination $destination -Force
Write-Host ''
Write-Host 'Installed CS2 Game State Integration config:' -ForegroundColor Green
Write-Host $destination -ForegroundColor Cyan
Write-Host ''
Write-Host 'Next: start run_overlay.bat, then fully restart CS2.' -ForegroundColor Yellow
