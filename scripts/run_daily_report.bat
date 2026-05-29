@echo off
REM run_daily_report.bat - 毎日 00:00 起動用バッチ（Windowsタスクスケジューラから呼ぶ）
REM 失敗してもタスクスケジューラに通知されるよう、ログを残しつつ exit code を保つ

cd /d "%~dp0\.."
if not exist logs mkdir logs

set LOG=logs\daily_report_%date:~0,4%%date:~5,2%%date:~8,2%.log

echo [%date% %time%] start >> "%LOG%"
python scripts\daily_trend_report.py >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] end rc=%RC% >> "%LOG%"
exit /b %RC%
