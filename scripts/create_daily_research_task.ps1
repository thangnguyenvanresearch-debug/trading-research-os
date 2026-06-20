param(
    [switch]$Register,
    [string]$TaskName = "TradingResearchOSDailyResearch",
    [string]$At = "08:00"
)

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Runner = Join-Path $ProjectRoot "scripts\run_daily_research_venv.ps1"
$Arguments = "-ExecutionPolicy Bypass -File `"$Runner`""

Write-Host "Daily research scheduled task preview"
Write-Host "Task name: $TaskName"
Write-Host "Working directory: $ProjectRoot"
Write-Host "Command: powershell.exe $Arguments"
Write-Host "Schedule time: $At"
Write-Host ""
Write-Host "This helper does not store passwords, API keys, cookies, or exchange credentials."
Write-Host "Default behavior is print-only. Use -Register to create the scheduled task."
Write-Host ""
Write-Host "Examples:"
Write-Host "  .\scripts\create_daily_research_task.ps1"
Write-Host "  .\scripts\create_daily_research_task.ps1 -Register -At `"08:30`""

if ($Register) {
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $Arguments -WorkingDirectory $ProjectRoot
    $Trigger = New-ScheduledTaskTrigger -Daily -At $At
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "Trading Research OS daily local research run" -Force
    Write-Host "Registered scheduled task: $TaskName"
} else {
    Write-Host "Printed only; no task was registered."
}
