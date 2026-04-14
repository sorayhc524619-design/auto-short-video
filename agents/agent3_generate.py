"""
agent3_generate.py - Agent 3: 並列生成エージェント
音声・映像・字幕データを asyncio で並列生成します。
フォールバック: VOICEVOX → ElevenLabs（音声）/ Kling AI → 黒背景（映像）
"""

import asyncio
import logging
import json
import os
import time
import struct
import wave
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import requests
import httpx

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class VoiceGenerator:
    """音声生成クラス（VOICEVOX優先、ElevenLabsフォールバック）"""

    def generate_with_voicevox(self, text: str, output_path: Path) -> bool:
        """VOICEVOXで音声生成"""
        try:
            # 音声合成クエリの作成
            query_resp = requests.post(
                f"{config.VOICEVOX_URL}/audio_query",
                params={"text": text, "speaker": config.VOICEVOX_SPEAKER_ID},
                timeout=30
            )
            query_resp.raise_for_status()
            query = query_resp.json()

            # 音声合成の実行
            synth_resp = requests.post(
                f"{config.VOICEVOX_URL}/synthesis",
                params={"speaker": config.VOICEVOX_SPEAKER_ID},
                json=query,
                timeout=60
            )
            synth_resp.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(synth_resp.content)

            logger.info(f"VOICEVOX音声生成成功: {output_path}")
            return True

        except Exception as e:
            logger.warning(f"VOICEVOX失敗: {e}")
            return False

    def generate_with_elevenlabs(self, text: str, output_path: Path) -> bool:
        """ElevenLabsで音声生成"""
        if not config.ELEVENLABS_API_KEY:
            logger.warning("ELEVENLABS_API_KEY が未設定")
            return False

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
            headers = {
                "xi-api-key": config.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "text": text,
                "model_id": config.ELEVENLABS_MODEL_ID,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(resp.content)

            logger.info(f"ElevenLabs音声生成成功: {output_path}")
            return True

        except Exception as e:
            logger.warning(f"ElevenLabs失敗: {e}")
            return False

    def generate_silent_audio(self, duration_sec: float, output_path: Path) -> bool:
        """無音のWAVファイルを生成（最終フォールバック）"""
        try:
            sample_rate = 44100
            num_channels = 1
            sample_width = 2  # 16bit

            with wave.open(str(output_path), "w") as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(sample_rate)
                frames = b"\x00\x00" * int(sample_rate * duration_sec)
                wf.writeframes(frames)

            logger.warning(f"無音音声ファイルを生成: {output_path}")
            return True
        except Exception as e:
            logger.error(f"無音音声生成失敗: {e}")
            return False

    def generate(self, text: str, output_path: Path, duration_sec: float = 5.0) -> Path:
        """フォールバック付き音声生成"""
        # VOICEVOX試行
        if self.generate_with_voicevox(text, output_path):
            return output_path

        # ElevenLabsフォールバック
        if self.generate_with_elevenlabs(text, output_path):
            return output_path

        # 最終フォールバック（無音）
        self.generate_silent_audio(duration_sec, output_path)
        return output_path


class VideoGenerator:
    """映像生成クラス（Kling AI優先、黒背景フォールバック）"""

    def generate_with_kling(self, prompt: str, duration_sec: int, output_path: Path) -> bool:
        """Kling AIで映像生成"""
        if not config.KLING_API_KEY:
            logger.warning("KLING_API_KEY が未設定")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {config.KLING_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "kling-v1",
                "prompt": prompt,
                "duration": min(duration_sec, 10),  # Kling AIの最大10秒制限
                "aspect_ratio": "9:16",
                "mode": "std",
            }

            # 生成リクエスト
            resp = requests.post(
                f"{config.KLING_API_BASE_URL}/videos/text2video",
                json=payload,
                headers=headers,
                timeout=30
            )
            resp.raise_for_status()
            task_id = resp.json().get("data", {}).get("task_id")

            if not task_id:
                raise ValueError("task_idが取得できませんでした")

            # ポーリングで完了を待つ（最大120秒）
            for _ in range(24):
                time.sleep(5)
                status_resp = requests.get(
                    f"{config.KLING_API_BASE_URL}/videos/text2video/{task_id}",
                    headers=headers,
                    timeout=30
                )
                status_resp.raise_for_status()
                status_data = status_resp.json().get("data", {})

                if status_data.get("task_status") == "succeed":
                    video_url = status_data["task_result"]["videos"][0]["url"]
                    video_resp = requests.get(video_url, timeout=60)
                    with open(output_path, "wb") as f:
                        f.write(video_resp.content)
                    logger.info(f"Kling AI映像生成成功: {output_path}")
                    return True

                elif status_data.get("task_status") == "failed":
                    raise RuntimeError("Kling AI生成タスクが失敗しました")

            raise TimeoutError("Kling AI生成タイムアウト")

        except Exception as e:
            logger.warning(f"Kling AI失敗: {e}")
            return False

    def generate_placeholder(self, text: str, duration_sec: int, output_path: Path) -> bool:
        """FFmpegで黒背景+テキストの動画を生成（最終フォールバック）"""
        try:
            import subprocess
            safe_text = text.replace("'", "").replace('"', "")[:30]

            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:size={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:duration={duration_sec}",
                "-vf", f"drawtext=text='{safe_text}':fontsize=60:fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
                "-c:v", "libx264",
                "-t", str(duration_sec),
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.warning(f"プレースホルダー動画生成: {output_path}")
            return True
        except Exception as e:
            logger.error(f"プレースホルダー生成失敗: {e}")
            return False

    def generate(self, prompt: str, duration_sec: int, output_path: Path, fallback_text: str = "") -> Path:
        """フォールバック付き映像生成"""
        if self.generate_with_kling(prompt, duration_sec, output_path):
            return output_path

        self.generate_placeholder(fallback_text or prompt[:30], duration_sec, output_path)
        return output_path


class SubtitleGenerator:
    """字幕生成クラス（Whisperを使用）"""

    def generate_from_audio(self, audio_path: Path, output_srt_path: Path) -> bool:
        """Whisperで音声から字幕(.srt)を生成"""
        try:
            import whisper

            logger.info(f"Whisperで字幕生成中: {audio_path}")
            model = whisper.load_model("small")
            result = model.transcribe(str(audio_path), language="ja")

            # SRTフォーマットで書き出し
            with open(output_srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(result["segments"], 1):
                    start = self._seconds_to_srt_time(segment["start"])
                    end = self._seconds_to_srt_time(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

            logger.info(f"字幕生成成功: {output_srt_path}")
            return True

        except Exception as e:
            logger.warning(f"Whisper字幕生成失敗: {e}")
            return False

    def generate_from_narration(self, narration_text: str, duration_sec: float, output_srt_path: Path) -> bool:
        """ナレーションテキストから簡易SRTを生成（Whisperのフォールバック）"""
        try:
            with open(output_srt_path, "w", encoding="utf-8") as f:
                f.write(f"1\n")
                f.write(f"00:00:00,000 --> {self._seconds_to_srt_time(duration_sec)}\n")
                f.write(f"{narration_text}\n\n")
            logger.info(f"簡易字幕生成: {output_srt_path}")
            return True
        except Exception as e:
            logger.error(f"字幕生成失敗: {e}")
            return False

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """秒数をSRT時間形式に変換"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class GenerateAgent:
    """音声・映像・字幕を並列生成するエージェント"""

    def __init__(self):
        self.voice_gen = VoiceGenerator()
        self.video_gen = VideoGenerator()
        self.subtitle_gen = SubtitleGenerator()
        self.temp_dir = config.TEMP_DIR

    async def generate_scene_assets(self, scene: Dict[str, Any], scene_dir: Path) -> Dict[str, Any]:
        """1シーンの音声・映像・字幕を並列生成"""
        scene_id = scene["scene_id"]
        duration = scene["duration_sec"]
        narration = scene["narration"]
        visual = scene.get("visual_direction", narration[:50])

        audio_path = scene_dir / f"scene_{scene_id}_audio.wav"
        video_path = scene_dir / f"scene_{scene_id}_video.mp4"
        srt_path = scene_dir / f"scene_{scene_id}_subtitle.srt"

        logger.info(f"シーン {scene_id} の並列生成開始...")

        # asyncio で並列実行
        loop = asyncio.get_event_loop()

        audio_task = loop.run_in_executor(
            None, self.voice_gen.generate, narration, audio_path, float(duration)
        )
        video_task = loop.run_in_executor(
            None, self.video_gen.generate, visual, duration, video_path, narration[:30]
        )

        # 音声と映像を並列生成
        audio_result, video_result = await asyncio.gather(audio_task, video_task)

        # 字幕は音声生成後に実行
        srt_result = await loop.run_in_executor(
            None, self._generate_subtitle, audio_path, narration, duration, srt_path
        )

        return {
            "scene_id": scene_id,
            "duration_sec": duration,
            "audio_path": str(audio_result),
            "video_path": str(video_result),
            "srt_path": str(srt_path) if srt_path.exists() else None,
            "narration": narration,
        }

    def _generate_subtitle(self, audio_path: Path, narration: str, duration: float, srt_path: Path) -> Optional[Path]:
        """字幕生成（Whisper優先、テキストフォールバック）"""
        if audio_path.exists():
            if self.subtitle_gen.generate_from_audio(audio_path, srt_path):
                return srt_path

        if self.subtitle_gen.generate_from_narration(narration, duration, srt_path):
            return srt_path

        return None

    async def run(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        全シーンの素材を並列生成します。

        Args:
            script_data: Agent 2の出力データ（scenes配列を含む）

        Returns:
            dict: 各シーンの素材パスを含むデータ
        """
        logger.info("=== Agent 3: 並列生成開始 ===")

        # 今日の日付でディレクトリ作成
        today = datetime.now().strftime("%Y%m%d")
        scene_dir = self.temp_dir / today
        scene_dir.mkdir(parents=True, exist_ok=True)

        scenes = script_data.get("scenes", [])
        if not scenes:
            raise ValueError("台本にシーンデータがありません")

        # 全シーンを並列処理
        tasks = [
            self.generate_scene_assets(scene, scene_dir)
            for scene in scenes
        ]
        scene_assets = await asyncio.gather(*tasks)

        result = {
            "title": script_data.get("title", ""),
            "description": script_data.get("description", ""),
            "hashtags": script_data.get("hashtags", []),
            "thumbnail_text": script_data.get("thumbnail_text", ""),
            "scene_assets": list(scene_assets),
            "scene_dir": str(scene_dir),
            "date": today,
        }

        logger.info(f"Agent 3 完了: {len(scene_assets)}シーンの素材生成完了")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # テスト用ダミーデータ
    dummy_script = {
        "title": "テスト動画",
        "description": "テスト",
        "hashtags": ["#テスト"],
        "scenes": [
            {
                "scene_id": 1,
                "duration_sec": 5,
                "type": "hook",
                "narration": "今日は驚きの豆知識をご紹介します！",
                "visual_direction": "明るい背景にタイトルテキスト",
            },
            {
                "scene_id": 2,
                "duration_sec": 10,
                "type": "main",
                "narration": "実は、タコは3つの心臓を持っているんです！",
                "visual_direction": "海の中を泳ぐタコの映像",
            },
        ]
    }

    agent = GenerateAgent()
    result = asyncio.run(agent.run(dummy_script))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
