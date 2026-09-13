param(
    [string]$OutputDirectory = "../output/pdf"
)

$ErrorActionPreference = "Stop"
$localBin = Join-Path $env:LOCALAPPDATA "Programs/MiKTeX/miktex/bin/x64"

function Resolve-Executable([string]$Name, [string]$FallbackPath) {
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($command -and $command.Path) {
        return $command.Path
    }
    if (Test-Path -LiteralPath $FallbackPath) {
        return (Get-Item -LiteralPath $FallbackPath).FullName
    }
    return $null
}

$pdfLatex = Resolve-Executable "pdflatex" (Join-Path $localBin "pdflatex.exe")
$bibtex = Resolve-Executable "bibtex" (Join-Path $localBin "bibtex.exe")
if (-not $pdfLatex -or -not $bibtex) {
    throw "pdflatex and bibtex are required"
}

$paperRoot = $PSScriptRoot
$output = [IO.Path]::GetFullPath((Join-Path $paperRoot $OutputDirectory))
New-Item -ItemType Directory -Force $output | Out-Null

function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable failed with exit code $LASTEXITCODE"
    }
}

Push-Location $paperRoot
try {
    $texArgs = @("--enable-installer", "--interaction=nonstopmode", "--halt-on-error", "-output-directory=$output")
    Invoke-Checked $pdfLatex ($texArgs + "manuscript.tex")
    Invoke-Checked $bibtex @((Join-Path $output "manuscript"))
    Invoke-Checked $pdfLatex ($texArgs + "manuscript.tex")
    Invoke-Checked $pdfLatex ($texArgs + "manuscript.tex")
    Invoke-Checked $pdfLatex ($texArgs + "supplement.tex")
    Invoke-Checked $pdfLatex ($texArgs + "supplement.tex")
}
finally {
    Pop-Location
}

Write-Output "PASS_LATEX_BUILD"
Write-Output (Join-Path $output "manuscript.pdf")
Write-Output (Join-Path $output "supplement.pdf")
