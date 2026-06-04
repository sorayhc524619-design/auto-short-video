"""
config.py - 設定ファイル
アメリカ向けBGMチャンネル（Cinematic Sleep Music）の自動生成パイプライン設定。
.env または GitHub Secrets から読み込みます。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ===== APIキー =====
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
YOUTUBE_CREDENTIALS_JSON = os.environ.get("YOUTUBE_CREDENTIALS_JSON", "")

# Suno API（音楽生成）- サードパーティ経由（sunoapi.org / aimlapi.com 等）
SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "")
SUNO_API_BASE_URL = os.environ.get("SUNO_API_BASE_URL", "https://api.sunoapi.org")
SUNO_MODEL = os.environ.get("SUNO_MODEL", "V5")  # V5 = v5.5系
SUNO_INSTRUMENTAL = os.environ.get("SUNO_INSTRUMENTAL", "true").lower() == "true"

# Stability AI（ビジュアル画像生成）
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")
STABILITY_API_BASE_URL = "https://api.stability.ai"

# ===== モックモード =====
# True にすると Claude/Suno/Stability API を呼ばず、ffmpegで合成した
# テスト用素材でパイプラインを通します。--mock CLI フラグで上書き可。
MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

# ===== ローカル素材モード =====
# LOCAL_MUSIC_DIR : 既にSuno UI等で生成したMP3/WAVを置いたディレクトリ
#                   → Agent2 はAPI呼ばずこのディレクトリの曲を使う
# LOCAL_IMAGE_PATH: ファイル or ディレクトリ。1920x1080に自動正規化
#                   → Agent3 は Stability 呼ばずこの画像を使う
LOCAL_MUSIC_DIR = os.environ.get("LOCAL_MUSIC_DIR", "")
LOCAL_IMAGE_PATH = os.environ.get("LOCAL_IMAGE_PATH", "")
# LOCAL_VIDEO_PATH: 既存のループ動画ファイル（mp4/mov/webm）。指定すると画像処理を完全スキップし、
# この動画を loop_base としてそのまま使う（target尺まで自動ループ）。
LOCAL_VIDEO_PATH = os.environ.get("LOCAL_VIDEO_PATH", "")

# ANIMATE_EFFECTS: 静止画→アニメーション化のエフェクト指定（カンマ区切り）
# rain, flicker, zoom, grain から選択。LOCAL_IMAGE_PATH と併用時のみ有効
ANIMATE_EFFECTS = os.environ.get("ANIMATE_EFFECTS", "")

# AMBIENT_OVERRIDE_PATH: 環境音ファイルを直接指定（Claudeのテーマ選択を上書き）
# 設定するとAMBIENT_FILESの選択を無視し、このファイルだけをMIXに使う
AMBIENT_OVERRIDE_PATH = os.environ.get("AMBIENT_OVERRIDE_PATH", "")

# ===== 装飾オフフラグ =====
# SKIP_AMBIENT: 環境音（雨/暖炉等）をミックスしない
# SKIP_TITLE  : タイトルカード（冒頭のフェードインテキスト）を入れない
SKIP_AMBIENT = os.environ.get("SKIP_AMBIENT", "").lower() in ("true", "1", "yes")
SKIP_TITLE = os.environ.get("SKIP_TITLE", "").lower() in ("true", "1", "yes")
SKIP_ZOOM = os.environ.get("SKIP_ZOOM", "").lower() in ("true", "1", "yes")

# ===== コンテンツ設定 =====
CHANNEL_NICHE = os.environ.get("CHANNEL_NICHE", "Cinematic Sleep Music")
CONTENT_LANGUAGE = "en"  # 米国向け（英語固定）
# 1動画あたりの目標尺（秒）。初回テストは 600（10分）推奨、本番は 28800（8h）
VIDEO_DURATION_SEC = int(os.environ.get("VIDEO_DURATION_SEC", "10800"))  # default 3h
# 1テーマあたりに Suno で生成する曲数（連結してループ）
MUSIC_TRACKS_PER_VIDEO = int(os.environ.get("MUSIC_TRACKS_PER_VIDEO", "5"))
# クロスフェード（秒）
MUSIC_CROSSFADE_SEC = int(os.environ.get("MUSIC_CROSSFADE_SEC", "6"))
# 環境音のミックス音量（0.0 - 1.0）
AMBIENT_VOLUME = float(os.environ.get("AMBIENT_VOLUME", "0.35"))
MUSIC_VOLUME = float(os.environ.get("MUSIC_VOLUME", "0.85"))

# ===== Claude API =====
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096

# ===== 動画設定（横型16:9） =====
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_BITRATE = "3500k"
AUDIO_BITRATE = "192k"

# ===== タイトルカード（イントロ） =====
TITLE_CARD_DURATION_SEC = 6
FONT_PATH = os.environ.get(
    "FONT_PATH",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
)
TITLE_FONT_SIZE = 84
TITLE_FONT_COLOR = "white"

# ===== YouTube設定 =====
YOUTUBE_CATEGORY_ID = "10"  # Music
YOUTUBE_PRIVACY_STATUS = os.environ.get("YOUTUBE_PRIVACY_STATUS", "public")
YOUTUBE_MADE_FOR_KIDS = False
YOUTUBE_DEFAULT_LANGUAGE = "en"

# ===== パス設定 =====
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TEMP_DIR = OUTPUT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 環境音アセット（ローカル配置）。ファイル名 = キー
# 例: ambient/rain.mp3, ambient/fireplace.mp3, ambient/forest.mp3, ambient/wind.mp3
AMBIENT_DIR = BASE_DIR / "ambient"
AMBIENT_DIR.mkdir(exist_ok=True)
AMBIENT_FILES = {
    "rain": AMBIENT_DIR / "rain.mp3",
    "fireplace": AMBIENT_DIR / "fireplace.mp3",
    "forest": AMBIENT_DIR / "forest.mp3",
    "wind": AMBIENT_DIR / "wind.mp3",
    "ocean": AMBIENT_DIR / "ocean.mp3",
    "thunder": AMBIENT_DIR / "thunder.mp3",
    "stream": AMBIENT_DIR / "stream.mp3",
    "none": None,
}

# ===== ログ設定 =====
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "pipeline.log"


def validate_config():
    """必須環境変数の確認"""
    errors = []
    if not CLAUDE_API_KEY:
        errors.append("CLAUDE_API_KEY が設定されていません")
    if not SUNO_API_KEY:
        errors.append("SUNO_API_KEY が設定されていません（音楽生成不可）")
    if not STABILITY_API_KEY:
        errors.append("STABILITY_API_KEY が設定されていません（画像はプレースホルダになります）")
    if not YOUTUBE_CREDENTIALS_JSON:
        errors.append("YOUTUBE_CREDENTIALS_JSON が設定されていません（YouTube投稿スキップ）")
    return errors


if __name__ == "__main__":
    warnings = validate_config()
    if warnings:
        print("Setup warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("All required settings OK.")
