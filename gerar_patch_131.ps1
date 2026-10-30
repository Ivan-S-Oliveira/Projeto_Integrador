param(
    [Parameter(Mandatory = $true)]
    [string]$BaseRef,

    [string]$HeadRef = "HEAD",

    [string]$Output = "patch_131.diff"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$files = @(
    "src/data/cohort_source.py",
    "src/data/supervised_artifact.py",
    "tests/test_cohort_source.py",
    "tests/test_supervised_artifact.py"
)

if (-not (Test-Path ".git")) {
    throw "Execute este script na raiz do repositorio Git."
}

& git rev-parse --verify "$BaseRef^{commit}" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "BaseRef invalido: $BaseRef"
}

& git rev-parse --verify "$HeadRef^{commit}" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "HeadRef invalido: $HeadRef"
}

$missing = @($files | Where-Object { -not (Test-Path $_) })
if ($missing.Count -gt 0) {
    throw "Arquivos ausentes: $($missing -join ', ')"
}

$patch = & git diff --no-ext-diff --binary --full-index $BaseRef $HeadRef -- @files
if ($LASTEXITCODE -ne 0) {
    throw "git diff falhou."
}

if ([string]::IsNullOrWhiteSpace(($patch -join "`n"))) {
    throw "O intervalo nao contem alteracoes nos quatro arquivos esperados. Revise BaseRef e HeadRef."
}

$patchText = ($patch -join "`n") + "`n"
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) $Output),
    $patchText,
    [System.Text.UTF8Encoding]::new($false)
)

& git apply --check --reverse $Output
if ($LASTEXITCODE -ne 0) {
    throw "O patch foi gerado, mas nao corresponde integralmente ao estado de HeadRef."
}

Write-Host "Patch gerado e verificado: $Output"
Write-Host "Base: $BaseRef"
Write-Host "Destino: $HeadRef"
Write-Host "Arquivos:"
$files | ForEach-Object { Write-Host " - $_" }
