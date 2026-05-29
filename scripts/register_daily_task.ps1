# register_daily_task.ps1
# Windowsタスクスケジューラに「毎日 00:00 起動 → BGMトレンドレポート生成」を登録
#
# 実行: 管理者権限の PowerShell で
#   cd C:\Users\soray\auto-short-video
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
#   .\scripts\register_daily_task.ps1
#
# 登録後の確認: タスクスケジューラ → タスクスケジューラ ライブラリ →
#   "BGM Daily Trend Report" を探す。手動実行できる。
#
# 削除する場合: Unregister-ScheduledTask -TaskName "BGM Daily Trend Report" -Confirm:$false

$TaskName  = "BGM Daily Trend Report"
$RepoRoot  = (Resolve-Path "$PSScriptRoot\..").Path
$BatPath   = Join-Path $RepoRoot "scripts\run_daily_report.bat"

if (-not (Test-Path $BatPath)) {
    Write-Error "Batch file not found: $BatPath"
    exit 1
}

# Action: バッチをリポジトリ直下から実行
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatPath`"" `
    -WorkingDirectory $RepoRoot

# Trigger: 毎日 00:00（深夜0時）
$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"

# Settings: スリープ復帰OK・電源不問・最大7時間で打ち切り
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 7) `
    -MultipleInstances IgnoreNew

# Principal: 対話ログインなしでも実行（PCが起動中である必要は引き続きあり）
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# 既存タスクがあれば置換
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task: $TaskName"
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Generate daily US BGM YouTube trend report (PPTX + XLSX). Runs at 00:00, completes well before 07:00."

Write-Host ""
Write-Host "OK: Registered '$TaskName' to run daily at 00:00"
Write-Host "    Reports will be written to: $RepoRoot\reports\"
Write-Host ""
Write-Host "Test run now? (recommended):"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "View status:"
Write-Host "  Get-ScheduledTaskInfo -TaskName '$TaskName'"
