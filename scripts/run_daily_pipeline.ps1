# =============================================================================
# run_daily_pipeline.ps1
# Mango Digital Twin — daily full pipeline refresh
#
# Usage:
#   .\scripts\run_daily_pipeline.ps1
#
# What it does:
#   1. Changes to the project root (E:\mango-digital-twin)
#   2. Activates the Python virtual environment (.venv)
#   3. Runs the full pipeline: python main.py
#      (fetches fresh raw data AND regenerates all downstream outputs)
#   4. Saves a timestamped log under logs\daily_pipeline\
#   5. Exits with code 0 on success, 1 on failure
#
# Schedule via Windows Task Scheduler — see docs\DAILY_REFRESH_WINDOWS.md
# =============================================================================

$ErrorActionPreference = "Stop"

# ── Project root ──────────────────────────────────────────────────────────────
$ProjectRoot = "E:\mango-digital-twin"

# ── Log setup ─────────────────────────────────────────────────────────────────
$Timestamp   = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogDir      = Join-Path $ProjectRoot "logs\daily_pipeline"
$LogFile     = Join-Path $LogDir "daily_pipeline_$Timestamp.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# ── Helper: write to both console and log file ───────────────────────────────
function Write-Log {
    param([string]$Message)
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $Line
    Add-Content -Path $LogFile -Value $Line
}

# ── Start ─────────────────────────────────────────────────────────────────────
Write-Log "===== Mango Digital Twin — daily pipeline refresh ====="
Write-Log "Project root : $ProjectRoot"
Write-Log "Log file     : $LogFile"
Write-Log "Run started  : $Timestamp"

# ── Validate project root ─────────────────────────────────────────────────────
if (-not (Test-Path $ProjectRoot)) {
    Write-Log "ERROR: Project root not found: $ProjectRoot"
    exit 1
}

Set-Location $ProjectRoot
Write-Log "Working directory: $(Get-Location)"

# ── Activate virtual environment ──────────────────────────────────────────────
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $VenvActivate)) {
    Write-Log "ERROR: Virtual environment not found at: $VenvActivate"
    Write-Log "       Create it with: python -m venv .venv"
    Write-Log "       Then install: .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

Write-Log "Activating virtual environment..."
& $VenvActivate
Write-Log "Python: $(python --version 2>&1)"

# ── Run the full pipeline ──────────────────────────────────────────────────────
Write-Log "Running: python main.py  (full fetch + regeneration)"
Write-Log "------------------------------------------------------"

$PipelineOutput = & python main.py 2>&1
$ExitCode = $LASTEXITCODE

# Write pipeline output to log (and echo to console)
$PipelineOutput | ForEach-Object {
    $Line = "[pipeline] $_"
    Write-Host $Line
    Add-Content -Path $LogFile -Value $Line
}

Write-Log "------------------------------------------------------"

# ── Result ────────────────────────────────────────────────────────────────────
if ($ExitCode -eq 0) {
    Write-Log "SUCCESS: Pipeline completed successfully (exit code 0)."
    Write-Log "         Processed outputs and pipeline_run_metadata.json updated."
    Write-Log "===== Run complete ====="
    exit 0
} else {
    Write-Log "FAILURE: Pipeline exited with code $ExitCode."
    Write-Log "         Check the log above and logs\daily_pipeline\ for details."
    Write-Log "         Common causes: network unavailable, API error, missing package,"
    Write-Log "         or Google Earth Engine authentication expired."
    Write-Log "===== Run FAILED ====="
    exit 1
}
