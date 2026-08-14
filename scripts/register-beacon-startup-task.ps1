Param(
  [string]$TaskName = "BeaconAutoStart"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $PSScriptRoot "start-beacon-auto.ps1"

if (-not (Test-Path $StartScript)) {
  throw "Missing start script: $StartScript"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Auto-start Beacon stack (Redis, API, worker, beat, dashboard)" -Force | Out-Null
Write-Host "Registered scheduled task: $TaskName"
