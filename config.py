"""
config.py - 設定ファイル
全APIキーと定数を管理します。
環境変数から読み込むため、.envファイルまたはGitHub Secretsで設定してください。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルの読み込み（ローカル実行時）
load_dotenv()

# ===== APIキー設定 =====
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
YOUTUBE_CREDENTIALS_JSON = os.environ.get("YOUTUBE_CREDENTIALS_JSON", "")
TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
KLING_API_KEY = os.environ.get("KLING_API_KEY", "")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")

# ===== VOICEVOX設定 =====
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
VOICEVOX_SPEAKER_ID = int(os.environ.get("VOICEVOX_SPEAKER_ID", "3"))  # ずんだもん

# ===== コンテンツ設定 =====
CONTENT_GENRE = os.environ.get("CONTENT_GENRE", "雑学・豆知識")
CONTENT_LANGUAGE = os.environ.get("CONTENT_LANGUAGE", "ja")
VIDEO_DURATION_SEC = int(os.environ.get("VIDEO_DURATION_SEC", "60"))
MAX_TREND_KEYWORDS = int(os.environ.get("MAX_TREND_KEYWORDS", "5"))

# ===== Claude API設定 =====
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096

# ===== 動画設定 =====
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_BITRATE = "4000k"

# ===== フォント設定（字幕用） =====
FONT_PATH = os.environ.get(
    "FONT_PATH",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"  # Linux
)
FONT_SIZE = 48
FONT_COLOR = "white"
FONT_STROKE_COLOR = "black"
FONT_STROKE_WIDTH = 2

# ===== YouTube設定 =====
YOUTUBE_CATEGORY_ID = "22"  # エンタメ
YOUTUBE_PRIVACY_STATUS = "public"  # public / private / unlisted
YOUTUBE_MADE_FOR_KIDS = False

# ===== TikTok設定 =====
TIKTOK_API_BASE_URL = "https://open.tiktokapis.com/v2"

# ===== ElevenLabs設定 =====
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# ===== Kling AI設定 =====
KLING_API_BASE_URL = "https://api.klingai.com/v1"

# ===== パス設定 =====
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TEMP_DIR = OUTPUT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

BGM_PATH = OUTPUT_DIR / "bgm.mp3"  # BGMファイル（任意）

# ===== ログ設定 =====
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "pipeline.log"

# ===== RSS フィード =====
RSS_FEEDS = [
    "https://www3.nhk.or.jp/rss/news/cat0.xml",       # NHKニュース
    "https://feeds.feedburner.com/narinari",            # なりなり
    "https://www.nicovideo.jp/tag/トレンド?rss=2.0",    # ニコニコ動画
]

# ===== Google Trends設定 =====
TRENDS_GEO = "JP"  # 日本
TRENDS_TIMEFRAME = "now 1-d"  # 過去1日
TRENDS_CATEGORY = 0  # 全カテゴリ

# ===== 必須設定チェック =====
def validate_config():
    """必須の環境変数が設定されているか確認します"""
    errors = []
    if not CLAUDE_API_KEY:
        errors.append("CLAUDE_API_KEY が設定されていません")
    if not YOUTUBE_CREDENTIALS_JSON:
        errors.append("YOUTUBE_CREDENTIALS_JSON が設定されていません（YouTube投稿をスキップ）")
    if not TIKTOK_ACCESS_TOKEN:
        errors.append("TIKTOK_ACCESS_TOKEN が設定されていません（TikTok投稿をスキップ）")
    return errors


if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("⚠️ 設定の警告:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("✅ 全ての必須設定が確認されました")
