param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassthroughArgs
)

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $ProjectRoot ".venv-openbb\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error ".venv-openbb Python was not found at: $Python"
    Write-Error "Create or repair .venv-openbb, then rerun this script."
    exit 1
}

try {
    $OllamaVersion = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 5
    Write-Host "Ollama available: true ($($OllamaVersion.version))"
}
catch {
    Write-Warning "Ollama is unavailable at http://localhost:11434. The pipeline will still run; Local AI will save a safe unavailable/failed memo if needed."
}

$DefaultArgs = @(
    "scripts/run_daily_research.py",
    "--symbols", "AAPL", "MSFT",
    "--provider", "yfinance",
    "--interval", "1d",
    "--task-type", "daily_research_note",
    "--model", "qwen2.5:3b"
)

$Arguments = if ($PassthroughArgs -and $PassthroughArgs.Count -gt 0) {
    @("scripts/run_daily_research.py") + $PassthroughArgs
}
else {
    $DefaultArgs
}

Write-Host "Project root: $ProjectRoot"
Write-Host "Python: $Python"
Write-Host "Command: $Python $($Arguments -join ' ')"

Push-Location $ProjectRoot
try {
    & $Python @Arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
