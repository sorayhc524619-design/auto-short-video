"""
agent2_music.py - Agent 2: Suno APIで音楽生成
テーマから複数曲を生成し、ローカルにダウンロードします。

想定エンドポイント (sunoapi.org 互換):
  POST /api/v1/generate     -> {"taskId": "..."}
  GET  /api/v1/generate/record-info?taskId=... -> {"data": {"status": "...", "response": {"sunoData": [{"audioUrl": "..."}]}}}

他プロバイダ（aimlapi.com 等）を使う場合は SUNO_API_BASE_URL と _request_generate / _poll
を差し替えてください。
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class SunoClient:
    """sunoapi.org 互換クライアント"""

    def __init__(self):
        self.api_key = config.SUNO_API_KEY
        self.base_url = config.SUNO_API_BASE_URL.rstrip("/")
        self.model = config.SUNO_MODEL
        self.instrumental = config.SUNO_INSTRUMENTAL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request_generate(self, prompt: str, title: str) -> str:
        payload = {
            "prompt": prompt,
            "style": prompt[:200],
            "title": title[:80],
            "customMode": True,
            "instrumental": self.instrumental,
            "model": self.model,
        }
        resp = requests.post(
            f"{self.base_url}/api/v1/generate",
            json=payload, headers=self.headers, timeout=60,
        )
        resp.raise_for_status()
        body = resp.json()
        task_id = body.get("data", {}).get("taskId") or body.get("taskId")
        if not task_id:
            raise RuntimeError(f"Suno generate: taskId なし: {body}")
        logger.info(f"Suno task 受付: taskId={task_id}")
        return task_id

    def _poll(self, task_id: str, max_wait_sec: int = 600) -> List[str]:
        """Suno タスクの完了をポーリング。完了時に audioUrl のリストを返す"""
        start = time.time()
        while time.time() - start < max_wait_sec:
            resp = requests.get(
                f"{self.base_url}/api/v1/generate/record-info",
                params={"taskId": task_id},
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            status = (data.get("status") or "").upper()
            if status in ("SUCCESS", "COMPLETE", "FIRST_SUCCESS"):
                items = (data.get("response") or {}).get("sunoData") or data.get("sunoData") or []
                urls = [it.get("audioUrl") for it in items if it.get("audioUrl")]
                if urls:
                    return urls
            if status in ("FAIL", "FAILED", "ERROR", "SENSITIVE_WORD_ERROR"):
                raise RuntimeError(f"Suno タスク失敗: {data}")
            logger.info(f"Suno 待機中 status={status} elapsed={int(time.time()-start)}s")
            time.sleep(15)
        raise TimeoutError(f"Suno taskId={task_id} がタイムアウト")

    def generate(self, prompt: str, title: str) -> List[str]:
        """1プロンプトから音源URLのリストを返す（通常2曲返ってくる）"""
        task_id = self._request_generate(prompt, title)
        return self._poll(task_id)

    @staticmethod
    def download(url: str, output_path: Path) -> Path:
        logger.info(f"音源ダウンロード: {url} -> {output_path.name}")
        r = requests.get(url, timeout=180, stream=True)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output_path


def _generate_mock_track(output: Path, duration_sec: int, seed: int) -> Path:
    """ffmpegで合成した「音楽もどき」を生成（モックモード用）"""
    import subprocess
    # 基音をseedごとに変える: 220-440Hz の音階
    notes = [220.0, 246.94, 277.18, 311.13, 329.63, 369.99, 415.30, 440.0]
    f1 = notes[seed % len(notes)]
    f2 = notes[(seed + 3) % len(notes)]
    f3 = notes[(seed + 5) % len(notes)]
    # 3つの正弦波 + 軽くトレモロ
    src = (
        f"sine=frequency={f1}:duration={duration_sec},"
        f"tremolo=f=0.5:d=0.4,"
        f"volume=0.3"
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", src,
        "-f", "lavfi", "-i", f"sine=frequency={f2}:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency={f3}:duration={duration_sec}",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=first[m1];"
        "[m1][2:a]amix=inputs=2:duration=first,volume=0.4[out]",
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    logger.info(f"[MOCK] 音楽もどき生成: {output.name} ({duration_sec}s)")
    return output


class MusicAgent:
    def __init__(self):
        if config.MOCK_MODE:
            self.client = None
            return
        if not config.SUNO_API_KEY:
            raise ValueError("SUNO_API_KEY が設定されていません")
        self.client = SunoClient()

    def run(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("=== Agent 2: 音楽生成開始 ===")
        date = theme.get("date")
        theme_name = theme.get("theme_name", "untitled")
        work_dir = config.TEMP_DIR / f"{date}_{theme_name}" / "music"
        work_dir.mkdir(parents=True, exist_ok=True)

        prompts = theme.get("music_prompts", [])
        if not prompts:
            raise ValueError("theme.music_prompts が空です")

        track_paths: List[Path] = []

        if config.MOCK_MODE:
            for i, _ in enumerate(prompts, 1):
                out = work_dir / f"track_{i:02d}.mp3"
                _generate_mock_track(out, duration_sec=90, seed=i)
                track_paths.append(out)
            result = dict(theme)
            result["music_tracks"] = [str(p) for p in track_paths]
            result["music_dir"] = str(work_dir)
            logger.info(f"Agent 2 完了 [MOCK]: {len(track_paths)}曲")
            return result

        for i, prompt in enumerate(prompts, 1):
            title = f"{theme.get('english_title', theme_name)} - Part {i}"
            try:
                urls = self.client.generate(prompt, title)
            except Exception as e:
                logger.error(f"曲{i}生成失敗（スキップ）: {e}")
                continue
            # 通常 Suno は 1 タスク 2 バリエーション → 最初のものを採用
            url = urls[0]
            out = work_dir / f"track_{i:02d}.mp3"
            self.client.download(url, out)
            track_paths.append(out)
            logger.info(f"曲{i}/{len(prompts)} ダウンロード完了")

        if not track_paths:
            raise RuntimeError("曲が1つも生成できませんでした")

        result = dict(theme)
        result["music_tracks"] = [str(p) for p in track_paths]
        result["music_dir"] = str(work_dir)
        logger.info(f"Agent 2 完了: {len(track_paths)}曲生成")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dummy = {
        "theme_name": "test",
        "date": "00000000",
        "english_title": "Test",
        "music_prompts": [
            "Calm jazz piano, smooth saxophone, 60 BPM, rainy night cafe ambience, instrumental, no vocals"
        ],
    }
    print(json.dumps(MusicAgent().run(dummy), default=str, indent=2))
