"""
agent3_visual.py - Agent 3: ビジュアル生成
Stability AI で 16:9 のシネマティック画像を 1〜3 枚生成し、
ffmpeg で Ken Burns 効果（ゆっくりズーム/パン）を付けてループ可能な短尺動画を作ります。
最終的な8時間ループは Agent 4 で組みます。
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


# Ken Burns loop duration (秒)。これを Agent 4 で繰り返し再生する
LOOP_BASE_DURATION_SEC = 60
NUM_IMAGE_VARIANTS = 3  # 同じテーマで微妙に違う絵を生成しループを単調にしない


class StabilityClient:
    def __init__(self):
        self.api_key = "" if config.MOCK_MODE else config.STABILITY_API_KEY
        self.base_url = config.STABILITY_API_BASE_URL.rstrip("/")

    def generate_image(self, prompt: str, output_path: Path, seed: int = 0) -> bool:
        if not self.api_key:
            if config.MOCK_MODE:
                logger.info("[MOCK] Stability APIスキップ→プレースホルダ画像へ")
            else:
                logger.warning("STABILITY_API_KEY 未設定")
            return False
        try:
            url = f"{self.base_url}/v2beta/stable-image/generate/core"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "image/*",
            }
            files = {"none": ""}
            data = {
                "prompt": prompt + ", cinematic, ultra detailed, moody lighting, no text, no watermark",
                "negative_prompt": "text, watermark, signature, ugly, blurry, low quality",
                "aspect_ratio": "16:9",
                "output_format": "png",
                "seed": str(seed),
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)
            if resp.status_code != 200:
                logger.error(f"Stability エラー {resp.status_code}: {resp.text[:200]}")
                return False
            output_path.write_bytes(resp.content)
            logger.info(f"画像生成: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Stability 失敗: {e}")
            return False


def generate_placeholder_image(prompt_text: str, output_path: Path) -> bool:
    """Stability 不可時のフォールバック: Pillowで暗背景＋テキスト画像を生成"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        img = Image.new("RGB", (w, h), color=(10, 20, 40))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(config.FONT_PATH, 64)
        except (OSError, IOError):
            font = ImageFont.load_default()
        safe = (prompt_text or "")[:60]
        bbox = draw.textbbox((0, 0), safe, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((w - tw) // 2, (h - th) // 2), safe, fill=(255, 255, 255), font=font)
        img.save(output_path)
        logger.warning(f"プレースホルダ画像: {output_path}")
        return True
    except Exception as e:
        logger.error(f"プレースホルダ画像失敗: {e}")
        return False


def make_kenburns_clip(image_path: Path, output_path: Path, duration_sec: int, direction: str = "in") -> bool:
    """1枚の画像から ゆっくりズーム/パン する短尺mp4を作る"""
    w, h, fps = config.VIDEO_WIDTH, config.VIDEO_HEIGHT, config.VIDEO_FPS
    total_frames = duration_sec * fps
    # zoompanはピクセル数の中間サイズに対する比率で動作。ゆるやかな zoom in
    if direction == "in":
        zoom_expr = f"min(zoom+0.00035,1.18)"
        xy = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    else:  # zoom out
        zoom_expr = f"if(eq(on,0),1.18,max(zoom-0.00035,1.0))"
        xy = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    vf = (
        f"scale=8000:-1,"
        f"zoompan=z='{zoom_expr}':{xy}:d={total_frames}:s={w}x{h}:fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Ken Burnsクリップ: {output_path.name} ({duration_sec}s)")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg失敗: {e.stderr.decode()[:500]}")
        return False


class VisualAgent:
    def __init__(self):
        self.stability = StabilityClient()

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("=== Agent 3: ビジュアル生成開始 ===")
        date = data.get("date")
        theme_name = data.get("theme_name", "untitled")
        work_dir = config.TEMP_DIR / f"{date}_{theme_name}" / "visual"
        work_dir.mkdir(parents=True, exist_ok=True)

        visual_prompt = data.get("visual_prompt") or data.get("scene_description") or "cozy room at night, warm lighting"

        image_paths: List[Path] = []
        clip_paths: List[Path] = []

        # ===== LOCAL_IMAGE_PATH: 手動で用意した画像を使う =====
        if config.LOCAL_IMAGE_PATH:
            src = Path(config.LOCAL_IMAGE_PATH).expanduser().resolve()
            if not src.exists():
                raise ValueError(f"LOCAL_IMAGE_PATH が存在しません: {src}")
            # ファイル or ディレクトリ両対応
            if src.is_dir():
                sources = sorted(list(src.glob("*.png")) + list(src.glob("*.jpg")) + list(src.glob("*.jpeg")))
            else:
                sources = [src]
            if not sources:
                raise ValueError(f"{src} に画像が見つかりません")
            logger.info(f"[LOCAL] {len(sources)} 枚の画像をローカルから読込: {src}")
            for i, s in enumerate(sources[:NUM_IMAGE_VARIANTS]):
                dst = work_dir / f"image_{i+1}.png"
                # ffmpeg で 1920x1080 に正規化（クロップ）
                import subprocess as _sp
                _sp.run([
                    "ffmpeg", "-y", "-i", str(s),
                    "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
                           f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}",
                    "-frames:v", "1", str(dst),
                ], check=True, capture_output=True)
                image_paths.append(dst)
        else:
            for i in range(NUM_IMAGE_VARIANTS):
                img_path = work_dir / f"image_{i+1}.png"
                ok = self.stability.generate_image(visual_prompt, img_path, seed=1000 + i * 137)
                if not ok:
                    generate_placeholder_image(data.get("thumbnail_text", visual_prompt), img_path)
                if img_path.exists():
                    image_paths.append(img_path)

        if not image_paths:
            raise RuntimeError("画像が1枚も用意できませんでした")

        # 各画像にKen Burns効果をつけてクリップ化（方向を交互に）
        for i, img in enumerate(image_paths):
            clip = work_dir / f"clip_{i+1}.mp4"
            direction = "in" if i % 2 == 0 else "out"
            if make_kenburns_clip(img, clip, LOOP_BASE_DURATION_SEC, direction):
                clip_paths.append(clip)

        if not clip_paths:
            raise RuntimeError("ループクリップが作成できませんでした")

        # 連結して 1 つの "loop base" mp4 にしておく
        loop_base = work_dir / "loop_base.mp4"
        list_file = work_dir / "concat.txt"
        with open(list_file, "w") as f:
            for c in clip_paths:
                f.write(f"file '{c.resolve()}'\n")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(loop_base),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"ループ基礎動画: {loop_base.name} (約{LOOP_BASE_DURATION_SEC * len(clip_paths)}s)")

        result = dict(data)
        result["image_paths"] = [str(p) for p in image_paths]
        result["loop_base_video"] = str(loop_base)
        result["loop_base_duration_sec"] = LOOP_BASE_DURATION_SEC * len(clip_paths)
        result["visual_dir"] = str(work_dir)
        logger.info(f"Agent 3 完了: 画像{len(image_paths)}枚 + ループ基礎動画")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dummy = {
        "date": "00000000",
        "theme_name": "test",
        "visual_prompt": "cozy japanese apartment at night with rain on window, warm lamp light",
    }
    print(VisualAgent().run(dummy))
