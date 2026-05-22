"""
agent5_upload.py - Agent 5: YouTube アップロード
英語メタデータ・Musicカテゴリ・カスタムサムネ対応で YouTube にアップロードします。
TikTok は長尺BGMには不向きなため削除（必要なら別途追加）。
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def generate_thumbnail(image_path: Path, overlay_text: str, output_path: Path) -> Optional[Path]:
    """既存の画像 + テキストオーバーレイで 1280x720 のサムネを作る"""
    if not image_path.exists():
        logger.warning("サムネ元画像なし")
        return None
    safe = overlay_text.replace("'", "").replace(":", "")[:60]
    vf = (
        f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        f"drawbox=x=0:y=540:w=iw:h=180:color=black@0.55:t=fill,"
        f"drawtext=fontfile={config.FONT_PATH}:text='{safe}':"
        f"fontsize=64:fontcolor=white:x=(w-tw)/2:y=600"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(image_path),
        "-vf", vf, "-frames:v", "1", str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"サムネ生成: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"サムネ生成失敗: {e.stderr.decode()[:300]}")
        return None


class YouTubeUploader:
    def __init__(self):
        self.credentials_json = config.YOUTUBE_CREDENTIALS_JSON

    def _service(self):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds_data = json.loads(self.credentials_json)
        creds = Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            scopes=creds_data.get("scopes", [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
            ]),
        )
        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list,
        thumbnail_path: Optional[Path] = None,
    ) -> Optional[str]:
        if not self.credentials_json:
            logger.warning("YOUTUBE_CREDENTIALS_JSON 未設定 → アップロードスキップ")
            return None
        if not video_path.exists():
            logger.error(f"動画なし: {video_path}")
            return None

        from googleapiclient.http import MediaFileUpload

        youtube = self._service()
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": [t[:30] for t in tags][:30],
                "categoryId": config.YOUTUBE_CATEGORY_ID,
                "defaultLanguage": config.YOUTUBE_DEFAULT_LANGUAGE,
                "defaultAudioLanguage": config.YOUTUBE_DEFAULT_LANGUAGE,
            },
            "status": {
                "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,
                "madeForKids": config.YOUTUBE_MADE_FOR_KIDS,
                "selfDeclaredMadeForKids": config.YOUTUBE_MADE_FOR_KIDS,
            },
        }
        media = MediaFileUpload(
            str(video_path), mimetype="video/mp4",
            resumable=True, chunksize=1024 * 1024 * 16,
        )
        logger.info(f"YouTube アップロード開始: {title}")
        req = youtube.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media,
        )
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                logger.info(f"upload {int(status.progress() * 100)}%")
        video_id = response.get("id")
        logger.info(f"アップロード成功: https://youtu.be/{video_id}")

        if thumbnail_path and thumbnail_path.exists():
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path)),
                ).execute()
                logger.info("サムネ設定完了")
            except Exception as e:
                logger.warning(f"サムネ設定失敗（収益化前は不可）: {e}")
        return video_id


class UploadAgent:
    def __init__(self):
        self.youtube = YouTubeUploader()

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("=== Agent 5: アップロード開始 ===")
        video_path = Path(data["final_video_path"])
        title = data.get("english_title", "Relaxing Sleep Music")
        description = data.get("description", "")
        tags = data.get("tags", [])

        # サムネ生成（最初の画像を使用）
        thumb_path = None
        if data.get("image_paths"):
            thumb_path = Path(data["visual_dir"]) / "thumbnail.jpg"
            generate_thumbnail(
                Path(data["image_paths"][0]),
                data.get("thumbnail_text") or title,
                thumb_path,
            )

        video_id = self.youtube.upload(video_path, title, description, tags, thumb_path)
        return {
            "youtube_video_id": video_id,
            "youtube_url": f"https://youtu.be/{video_id}" if video_id else None,
            "title": title,
            "video_path": str(video_path),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Agent 5 は前段の出力が必要です。main.py から実行してください。")
