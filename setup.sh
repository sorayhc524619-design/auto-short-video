#!/usr/bin/env bash
# setup.sh - ワンコマンドセットアップ
# ffmpeg/Python依存/環境音生成/.env雛形 を一気に整える。
# 手動でやるしかないもの（APIキー取得等）はこのスクリプトの最後で案内。

set -e

cd "$(dirname "$0")"

echo "=== BGM Pipeline Setup ==="
echo

# ===== 1. ffmpeg =====
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg が見つかりません。以下を実行してインストールしてください:"
  echo "  macOS:  brew install ffmpeg"
  echo "  Ubuntu: sudo apt-get install -y ffmpeg fonts-dejavu-core"
  echo "  Windows(Choco): choco install ffmpeg"
  exit 1
fi
echo "[OK] ffmpeg: $(ffmpeg -version | head -1)"

# ===== 2. Python依存 =====
echo "[..] pip install -r requirements.txt"
python3 -m pip install -q -r requirements.txt
echo "[OK] Python dependencies"

# ===== 3. .env 雛形 =====
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[OK] .env を作成しました（.env.example をコピー）"
  echo "     → 後でエディタで開いてAPIキーを記入してください"
else
  echo "[OK] .env は既存（変更しません）"
fi

# ===== 4. 環境音を合成 =====
echo "[..] 環境音を ffmpeg で合成中..."
python3 scripts/generate_ambient.py
echo "[OK] ambient/*.mp3 生成完了"

# ===== 5. モックパイプラインで動作確認 =====
echo
echo "=== モックモードで30秒のテスト動画を生成します ==="
echo "    （Claude/Suno/Stability APIは呼びません）"
echo
MOCK_MODE=true python3 main.py --mock --duration 30 || {
  echo "[FAIL] モックパイプラインが失敗しました。エラーログ↑を確認してください。"
  exit 1
}
echo
echo "=== セットアップ完了 ==="
echo
LATEST=$(ls -t output/final_*.mp4 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  echo "生成されたテスト動画: $LATEST"
  echo "  → 再生して、ffmpegパイプラインが動いていることを確認してください"
fi
echo
echo "次のステップ（あなた本人がやる必要があるもの）:"
echo "  1. Claude APIキー失効＆再発行: https://console.anthropic.com/settings/keys"
echo "  2. YouTube OAuth削除: https://myaccount.google.com/permissions"
echo "  3. GCP Client Secret再生成: https://console.cloud.google.com/apis/credentials"
echo "  4. Suno Pro登録: https://suno.ai (+ sunoapi.org でAPIキー取得)"
echo "  5. Stability AI登録: https://platform.stability.ai/account/keys"
echo
echo "上記5つが終わったら .env に新キーを記入して:"
echo "  python scripts/check_setup.py        # 全項目グリーン確認"
echo "  python main.py --dry-run --duration 600  # 本物APIで10分尺生成"
