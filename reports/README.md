# Daily BGM Trend Reports

毎日 0:00 に自動生成される US BGM YouTube トレンドレポート。

## ファイル

各日付ごとに3ファイル生成されます:

- `YYYYMMDD_bgm_trend.pptx` - PowerPoint（スライド版、視覚的に確認）
- `YYYYMMDD_bgm_trend.xlsx` - Excel（3シート: Top10 / 共通点 / 今日の行動計画）
- `YYYYMMDD_bgm_trend.json` - 生データ（パイプラインから直接使える）

## 自動化のセットアップ（Windows）

### 1. 一度だけ実行（管理者権限の PowerShell）

```powershell
cd C:\Users\soray\auto-short-video
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\register_daily_task.ps1
```

→ 「BGM Daily Trend Report」というタスクが登録される。

### 2. テスト実行（今すぐ動かす）

```powershell
Start-ScheduledTask -TaskName "BGM Daily Trend Report"
```

→ 数分後に `reports/` に新しいファイルが出る。

### 3. ステータス確認

```powershell
Get-ScheduledTaskInfo -TaskName "BGM Daily Trend Report"
```

### 4. 削除

```powershell
Unregister-ScheduledTask -TaskName "BGM Daily Trend Report" -Confirm:$false
```

## 前提条件

- `.env` に有効な `CLAUDE_API_KEY` が設定されていること
- PC が 00:00〜07:00 の間に起動していること
  - スリープ中でも `WakeToRun` 設定で自動復帰します
  - 完全シャットダウンしている場合は次回起動時に自動実行されます (`StartWhenAvailable`)

## 出力タイミング

- 00:00 に起動
- 数分〜10分程度で完了（Claude API への 1 リクエストのみ）
- 07:00 までには確実に完成
- 朝起きてすぐ `reports/` フォルダから当日の判断材料が読める

## 失敗時の確認

実行ログは `logs/daily_report_YYYYMMDD.log` に保存されます。
タスクスケジューラ画面の「履歴」タブからも実行結果が見られます。
