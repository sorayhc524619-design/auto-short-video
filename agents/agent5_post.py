"""
agent5_post.py - Agent 5: 自動投稿エージェント
YouTube Data API v3 と TikTok Content Posting API に動画を自動アップロードします。
"""

import logging
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class YouTubeUploader:
    """YouTube Data API v3 を使った動画アップロード"""

    def __init__(self):
        self.credentials_json = config.YOUTUBE_CREDENTIALS_JSON

    def _get_service(self):
        """YouTube APIサービスを初期化"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds_data = json.loads(self.credentials_json)
            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                scopes=creds_data.get("scopes", ["https://www.googleapis.com/auth/youtube.upload"])
            )
            return build("youtube", "v3", credentials=credentials)
        except Exception as e:
            logger.error(f"YouTube APIサービス初期化失敗: {e}")
            raise

    def upload(self, video_path: Path, title: str, description: str, hashtags: list) -> Optional[str]:
        """
        動画をYouTube Shortsにアップロードします。

        Returns:
            str: アップロードされた動画のYouTube ID、失敗時はNone
        """
        if not self.credentials_json:
            logger.warning("YOUTUBE_CREDENTIALS_JSON が未設定 → YouTube投稿スキップ")
            return None

        if not video_path.exists():
            logger.error(f"動画ファイルが見つかりません: {video_path}")
            return None

        try:
            from googleapiclient.http import MediaFileUpload

            youtube = self._get_service()

            # ハッシュタグを説明文に追加
            tags = [tag.lstrip("#") for tag in hashtags]
            full_description = f"{description}\n\n{' '.join(hashtags)}"

            body = {
                "snippet": {
                    "title": title[:100],  # YouTubeのタイトル上限100文字
                    "description": full_description[:5000],
                    "tags": tags,
                    "categoryId": config.YOUTUBE_CATEGORY_ID,
                    "defaultLanguage": "ja",
                },
                "status": {
                    "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,
                    "madeForKids": config.YOUTUBE_MADE_FOR_KIDS,
                    "selfDeclaredMadeForKids": config.YOUTUBE_MADE_FOR_KIDS,
                }
            }

            media = MediaFileUpload(
                str(video_path),
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024 * 8  # 8MBチャンク
            )

            logger.info(f"YouTube アップロード開始: {title}")
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"YouTube アップロード進捗: {progress}%")

            video_id = response.get("id")
            video_url = f"https://www.youtube.com/shorts/{video_id}"
            logger.info(f"YouTube アップロード成功: {video_url}")
            return video_id

        except Exception as e:
            logger.error(f"YouTube アップロード失敗: {e}")
            return None


class TikTokUploader:
    """TikTok Content Posting API を使った動画アップロード"""

    def __init__(self):
        self.access_token = config.TIKTOK_ACCESS_TOKEN
        self.base_url = config.TIKTOK_API_BASE_URL

    def upload(self, video_path: Path, title: str, hashtags: list) -> Optional[str]:
        """
        動画をTikTokに投稿します。

        Returns:
            str: publish_id、失敗時はNone
        """
        if not self.access_token:
            logger.warning("TIKTOK_ACCESS_TOKEN が未設定 → TikTok投稿スキップ")
            return None

        if not video_path.exists():
            logger.error(f"動画ファイルが見つかりません: {video_path}")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # ステップ1: アップロード初期化
            file_size = video_path.stat().st_size
            init_payload = {
                "post_info": {
                    "title": title[:150],  # TikTokのキャプション上限
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1,
                }
            }

            logger.info("TikTok アップロード初期化中...")
            init_resp = requests.post(
                f"{self.base_url}/post/publish/video/init/",
                json=init_payload,
                headers=headers,
                timeout=30
            )
            init_resp.raise_for_status()
            init_data = init_resp.json().get("data", {})
            publish_id = init_data.get("publish_id")
            upload_url = init_data.get("upload_url")

            if not publish_id or not upload_url:
                raise ValueError("publish_id または upload_url が取得できませんでした")

            # ステップ2: 動画ファイルをアップロード
            logger.info(f"TikTok 動画アップロード中: {video_path.name}")
            with open(video_path, "rb") as f:
                video_data = f.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size-1}/{file_size}",
                "Content-Length": str(file_size),
            }
            upload_resp = requests.put(
                upload_url,
                data=video_data,
                headers=upload_headers,
                timeout=120
            )
            upload_resp.raise_for_status()

            # ステップ3: 投稿ステータスを確認
            for _ in range(12):
                time.sleep(5)
                status_resp = requests.post(
                    f"{self.base_url}/post/publish/status/fetch/",
                    json={"publish_id": publish_id},
                    headers=headers,
                    timeout=30
                )
                status_resp.raise_for_status()
                status_data = status_resp.json().get("data", {})
                status = status_data.get("status")

                if status == "PUBLISH_COMPLETE":
                    logger.info(f"TikTok 投稿成功: publish_id={publish_id}")
                    return publish_id
                elif status in ["FAILED", "PUBLISH_FAILED"]:
                    raise RuntimeError(f"TikTok投稿失敗: {status_data}")

                logger.info(f"TikTok 投稿ステータス: {status}")

            logger.warning("TikTok 投稿タイムアウト（処理中の可能性あり）")
            return publish_id

        except Exception as e:
            logger.error(f"TikTok アップロード失敗: {e}")
            return None


class PostAgent:
    """YouTube と TikTok への自動投稿エージェント"""

    def __init__(self):
        self.youtube = YouTubeUploader()
        self.tiktok = TikTokUploader()

    def run(self, edit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        最終動画を各プラットフォームに投稿します。

        Args:
            edit_data: Agent 4の出力データ

        Returns:
            dict: 投稿結果（各プラットフォームのURL・ID）
        """
        logger.info("=== Agent 5: 自動投稿開始 ===")

        video_path = Path(edit_data.get("final_video_path", ""))
        title = edit_data.get("title", "今日の動画")
        description = edit_data.get("description", "")
        hashtags = edit_data.get("hashtags", ["#shorts"])

        results = {
            "youtube": None,
            "tiktok": None,
            "title": title,
            "video_path": str(video_path),
        }

        # YouTube Shorts アップロード
        youtube_id = self.youtube.upload(video_path, title, description, hashtags)
        if youtube_id:
            results["youtube"] = {
                "video_id": youtube_id,
                "url": f"https://www.youtube.com/shorts/{youtube_id}",
            }

        # TikTok アップロード
        tiktok_id = self.tiktok.upload(video_path, title, hashtags)
        if tiktok_id:
            results["tiktok"] = {
                "publish_id": tiktok_id,
            }

        logger.info(f"Agent 5 完了: YouTube={results['youtube']}, TikTok={results['tiktok']}")
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Agent 5 (自動投稿) は動画ファイルが必要です。main.py から実行してください。")
