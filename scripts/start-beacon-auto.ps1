Param(
  [switch]$WithDashboard = $true
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $RepoRoot "apps\api"
$WorkerDir = Join-Path $RepoRoot "apps\worker"
$DashboardDir = Join-Path $RepoRoot "apps\dashboard"

$env:POSTGRES_HOST = "127.0.0.1"
$env:REDIS_HOST = "127.0.0.1"
$env:POSTGRES_DB = "beacon"
$env:POSTGRES_USER = "beacon"
$env:POSTGRES_PASSWORD = "beacon_password"
$env:PYTHONPATH = "$RepoRoot\apps\api;$RepoRoot\apps\worker;$RepoRoot\packages;$RepoRoot"

function Start-IfNotRunning {
  param(
    [string]$Title,
    [string]$Match
  )
  $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$Match*" }
  if ($running) {
    Write-Host "$Title already running"
    return $false
  }
  return $true
}

Write-Host "1) Starting Redis..."
& (Join-Path $PSScriptRoot "start-redis.bat")

Write-Host "2) Applying DB migrations..."
Push-Location $ApiDir
python -m alembic -c alembic.ini upgrade head
Pop-Location

Write-Host "3) Starting API..."
if (Start-IfNotRunning -Title "API" -Match "uvicorn app.main:app --host 127.0.0.1 --port 8000") {
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Set-Location '$ApiDir'; `$env:POSTGRES_HOST='127.0.0.1'; `$env:REDIS_HOST='127.0.0.1'; `$env:PYTHONPATH='$env:PYTHONPATH'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
  )
}

Write-Host "4) Starting Celery worker..."
if (Start-IfNotRunning -Title "Celery worker" -Match "celery_app.celery_app worker --loglevel=INFO --pool=solo -Q celery") {
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Set-Location '$WorkerDir'; `$env:POSTGRES_HOST='127.0.0.1'; `$env:REDIS_HOST='127.0.0.1'; `$env:PYTHONPATH='$env:PYTHONPATH'; python -m celery -A worker.celery_app.celery_app worker --loglevel=INFO --pool=solo -Q celery"
  )
}

Write-Host "5) Starting Celery beat..."
if (Start-IfNotRunning -Title "Celery beat" -Match "celery_app.celery_app beat --loglevel=INFO") {
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Set-Location '$WorkerDir'; `$env:POSTGRES_HOST='127.0.0.1'; `$env:REDIS_HOST='127.0.0.1'; `$env:PYTHONPATH='$env:PYTHONPATH'; python -m celery -A worker.celery_app.celery_app beat --loglevel=INFO"
  )
}

if ($WithDashboard) {
  Write-Host "6) Starting dashboard..."
  if (Start-IfNotRunning -Title "Dashboard" -Match "next dev") {
    Start-Process powershell -WindowStyle Minimized -ArgumentList @(
      "-NoProfile",
      "-Command",
      "Set-Location '$RepoRoot'; npm run dashboard:dev"
    )
  }
}

Write-Host ""
Write-Host "Beacon auto-start completed."
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Dashboard: http://localhost:3000"
