$ErrorActionPreference = 'Stop'
$targetName = 'gamestate_integration_cs2_obs_overlay.cfg'
$steamRoots = New-Object System.Collections.Generic.List[string]
foreach ($key in @('HKCU:\Software\Valve\Steam','HKLM:\SOFTWARE\WOW6432Node\Valve\Steam','HKLM:\SOFTWARE\Valve\Steam')) {
    try {
        $item = Get-ItemProperty -Path $key -ErrorAction Stop
        foreach ($property in @('SteamPath','InstallPath')) {
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
$removed = $false
foreach ($lib in $libraryRoots) {
    $candidate = Join-Path $lib "steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\$targetName"
    if (Test-Path $candidate) { Remove-Item $candidate -Force; Write-Host "Removed $candidate" -ForegroundColor Green; $removed = $true }
}
if (-not $removed) { Write-Host 'Overlay GSI config was not found. Nothing to remove.' -ForegroundColor Yellow }
