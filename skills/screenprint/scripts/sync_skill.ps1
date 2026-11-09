# Mirror this skill into both agent homes, so DSH and Codex see the same files.
#
#   pwsh sync_skill.ps1                 # copy screenprint to ~/.codex/skills and ~/.dsh/skills
#   pwsh sync_skill.ps1 -Name my-skill   # same for any skill folder next to this script
#
# Run it from the skill folder (the folder that contains SKILL.md).

param(
    [string]$Name = "screenprint",
    [string]$Source = (Split-Path -Parent $PSScriptRoot),
    [switch]$WhatIf
)

$targets = @(
    (Join-Path $env:USERPROFILE ".codex\skills"),
    (Join-Path $env:USERPROFILE ".dsh\skills")
)

foreach ($root in $targets) {
    $dest = Join-Path $root $Name
    $srcFull = (Resolve-Path -LiteralPath $Source).Path.TrimEnd('\')
    $dstFull = [System.IO.Path]::GetFullPath($dest).TrimEnd('\')
    if ($srcFull -eq $dstFull) {
        Write-Host ("{0}  (source is this copy, nothing to do)" -f $dstFull)
        continue
    }
    Write-Host ("{0} -> {1}" -f $srcFull, $dstFull)
    if ($WhatIf) { continue }
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    if (Test-Path $dstFull) {
        $stamp = Get-Date -Format "yyyyMMddHHmmss"
        Rename-Item -LiteralPath $dstFull -NewName ("{0}.bak-{1}" -f $Name, $stamp)
    }
    Copy-Item -LiteralPath $srcFull -Destination $dstFull -Recurse -Force -Exclude '__pycache__'
    Get-ChildItem -LiteralPath $dstFull -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    $files = (Get-ChildItem -LiteralPath $dstFull -Recurse -File).Count
    Write-Host ("   copied {0} files" -f $files)
}

Write-Host ""
Write-Host "Verify:"
Write-Host ("   Get-Content '{0}' -TotalCount 6" -f (Join-Path $env:USERPROFILE ".codex\skills\$Name\SKILL.md"))
Write-Host ("   Get-Content '{0}' -TotalCount 6" -f (Join-Path $env:USERPROFILE ".dsh\skills\$Name\SKILL.md"))
