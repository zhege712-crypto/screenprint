# Export a deck with PowerPoint COM: slide PNGs and/or PDFs.
#
#   pwsh export.ps1 -Pptx deck.pptx -OutDir out\png -Png
#   pwsh export.ps1 -Pptx deck.pptx -OutDir out -Pdf -AllPdf out\all30.pdf -MainPdf out\main21.pdf -MainPages 21
#
# Notes
#   * One SaveAs(...,32) per open presentation  ->  each PDF gets its own COM session.
#   * Slide.Export renders the FINAL animation state; animations cannot be verified here.
#   * Use -MainPages to strip hidden backup pages from the printable PDF.

param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [switch]$Png,
    [switch]$Pdf,
    [string]$AllPdf,
    [string]$MainPdf,
    [int]$MainPages = 0,
    [int]$Width = 1600,
    [int]$Height = 900
)

function New-PowerPoint {
    $pp = New-Object -ComObject PowerPoint.Application
    return $pp
}

function Close-PowerPoint($pp) {
    try { $pp.Quit() } catch {}
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if ($Png) {
    $pp = New-PowerPoint
    $pres = $pp.Presentations.Open($Pptx, $true, $false, $false)
    $count = $pres.Slides.Count
    for ($i = 1; $i -le $count; $i++) {
        $path = Join-Path $OutDir ("p{0:d2}.png" -f $i)
        $pres.Slides.Item($i).Export($path, "PNG", $Width, $Height)
    }
    $pres.Close()
    Close-PowerPoint $pp
    Write-Host ("exported {0} pages to {1}" -f $count, $OutDir)
}

if ($Pdf -and $AllPdf) {
    $pp = New-PowerPoint
    $pres = $pp.Presentations.Open($Pptx, $true, $false, $false)
    foreach ($s in $pres.Slides) { $s.SlideShowTransition.Hidden = 0 }
    $pres.PrintOptions.PrintHiddenSlides = -1
    $pres.SaveAs((Resolve-Path -LiteralPath $OutDir).Path + "\" + (Split-Path -Leaf $AllPdf), 32)
    $pres.Close()
    Close-PowerPoint $pp
    Write-Host "wrote all-pages PDF"
}

if ($Pdf -and $MainPdf -and $MainPages -gt 0) {
    $pp = New-PowerPoint
    $pres = $pp.Presentations.Open($Pptx, $true, $false, $false)
    for ($i = $MainPages + 1; $i -le $pres.Slides.Count; $i++) {
        $pres.Slides.Item($i).SlideShowTransition.Hidden = -1
    }
    $pres.PrintOptions.PrintHiddenSlides = 0
    $pres.SaveAs((Resolve-Path -LiteralPath $OutDir).Path + "\" + (Split-Path -Leaf $MainPdf), 32)
    $pres.Close()
    Close-PowerPoint $pp
    Write-Host ("wrote main-pages PDF ({0} pages)" -f $MainPages)
}
