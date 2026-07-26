# ==============================
# setup.ps1 - one-click Windows setup
# ==============================
# Run from the project root after `git pull`:
#   .\setup.ps1
# Creates the virtual environment, installs dependencies, sets up .env if
# missing, and runs doctor.py to confirm everything is healthy.

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

$expectedVersion = (Get-Content ".python-version" -ErrorAction SilentlyContinue)
$expectedMajorMinor = ($expectedVersion -split '\.')[0..1] -join '.'

Write-Step "Locating Python $expectedVersion"
$pythonCmd = $null
foreach ($candidate in @("py -$expectedMajorMinor", "python")) {
    $parts = $candidate.Split(" ")
    if (Get-Command $parts[0] -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}
if (-not $pythonCmd) {
    Write-Host "No Python interpreter found on PATH. Install Python $expectedVersion first." -ForegroundColor Red
    exit 1
}
Write-Host "Using: $pythonCmd"

Write-Step "Creating virtual environment (.venv)"
if (-not (Test-Path ".venv")) {
    Invoke-Expression "$pythonCmd -m venv .venv"
} else {
    Write-Host ".venv already exists, skipping creation"
}

Write-Step "Activating virtual environment"
. .\.venv\Scripts\Activate.ps1

Write-Step "Installing dependencies"
pip install -r requirements.txt

Write-Step "Setting up .env"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env created from .env.example - add your PUBG_API_KEY before running main.py" -ForegroundColor Yellow
} else {
    Write-Host ".env already exists, skipping"
}

Write-Step "Running environment doctor"
python doctor.py
$doctorExitCode = $LASTEXITCODE

if ($doctorExitCode -eq 0) {
    Write-Host ""
    Write-Host "Setup complete. Try it out:" -ForegroundColor Green
    Write-Host "  python solo.py PlayerName" -ForegroundColor Green
    Write-Host "  python squad.py YourName Teammate1 Teammate2" -ForegroundColor Green
    Write-Host "(python main.py PlayerName gives the full raw stats dump instead)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Setup finished but the doctor found issues - see above." -ForegroundColor Yellow
}

exit $doctorExitCode
