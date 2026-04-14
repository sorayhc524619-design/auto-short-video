"""
agent4_edit.py - Agent 4: 動画編集エージェント
FFmpeg / MoviePy でシーン素材を結合し、字幕・BGMを追加して最終動画を生成します。
出力: output/final_YYYYMMDD.mp4 （1080x1920、縦型9:16）
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class EditAgent:
    """動画編集エージェント"""

    def __init__(self):
        self.output_dir = config.OUTPUT_DIR
        self.temp_dir = config.TEMP_DIR
        self.width = config.VIDEO_WIDTH
        self.height = config.VIDEO_HEIGHT
        self.fps = config.VIDEO_FPS

    def _run_ffmpeg(self, cmd: List[str], description: str = "") -> bool:
        """FFmpegコマンドを実行"""
        try:
            logger.info(f"FFmpeg実行: {description}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug(f"FFmpeg stdout: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg失敗 ({description}): {e.stderr}")
            return False

    def normalize_video(self, video_path: Path, output_path: Path, duration_sec: int) -> bool:
        """動画を9:16縦型にリサイズ・クロップし、指定秒数に調整"""
        if not video_path.exists():
            logger.warning(f"動画ファイルが見つかりません: {video_path}")
            # 黒背景を生成
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:size={self.width}x{self.height}:duration={duration_sec}:r={self.fps}",
                "-c:v", "libx264",
                str(output_path)
            ]
            return self._run_ffmpeg(cmd, "黒背景生成")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-t", str(duration_sec),
            "-vf", (
                f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},"
                f"fps={self.fps}"
            ),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",  # 音声なし（後で追加）
            str(output_path)
        ]
        return self._run_ffmpeg(cmd, f"動画正規化: {video_path.name}")

    def merge_audio_video(self, video_path: Path, audio_path: Path, output_path: Path, duration_sec: int) -> bool:
        """動画と音声を結合"""
        if not audio_path.exists():
            logger.warning(f"音声ファイルが見つかりません: {audio_path}")
            # 動画のみコピー
            cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]
            return self._run_ffmpeg(cmd, "動画コピー（音声なし）")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-t", str(duration_sec),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        return self._run_ffmpeg(cmd, f"音声結合: {audio_path.name}")

    def burn_subtitles(self, video_path: Path, srt_path: Path, output_path: Path) -> bool:
        """SRT字幕を動画に焼き込む"""
        if not srt_path or not srt_path.exists():
            logger.info("字幕ファイルなし、スキップ")
            # 動画をそのままコピー
            cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]
            return self._run_ffmpeg(cmd, "動画コピー（字幕なし）")

        # Windowsパス対応: SRTファイルをシンプルなtempパスにコピーしてFFmpegに渡す
        import tempfile, shutil
        tmp_srt = Path(tempfile.gettempdir()) / f"sub_{srt_path.stem}.srt"
        shutil.copy2(srt_path, tmp_srt)
        # FFmpeg用パス変換（Windowsのコロンをエスケープ）
        srt_ffmpeg = str(tmp_srt).replace("\\", "/").replace(":", "\\:")

        subtitle_filter = (
            f"subtitles='{srt_ffmpeg}':"
            f"force_style='FontSize={config.FONT_SIZE},"
            f"PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,"
            f"Outline={config.FONT_STROKE_WIDTH},"
            f"Alignment=2'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-c:a", "copy",
            str(output_path)
        ]

        success = self._run_ffmpeg(cmd, f"字幕焼き込み: {srt_path.name}")
        if not success:
            # 字幕焼き込み失敗時は字幕なしでコピー
            logger.warning("字幕焼き込み失敗、字幕なしで続行")
            cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]
            return self._run_ffmpeg(cmd, "動画コピー（字幕失敗フォールバック）")

        return True

    def concatenate_scenes(self, scene_video_paths: List[Path], output_path: Path) -> bool:
        """複数シーンの動画を結合"""
        if not scene_video_paths:
            raise ValueError("結合するシーンがありません")

        if len(scene_video_paths) == 1:
            cmd = ["ffmpeg", "-y", "-i", str(scene_video_paths[0]), "-c", "copy", str(output_path)]
            return self._run_ffmpeg(cmd, "シングルシーンコピー")

        # concatフィルターを使用
        inputs = []
        for p in scene_video_paths:
            inputs += ["-i", str(p)]

        n = len(scene_video_paths)
        filter_complex = "".join([f"[{i}:v][{i}:a]" for i in range(n)])
        filter_complex += f"concat=n={n}:v=1:a=1[v][a]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            str(output_path)
        ]
        return self._run_ffmpeg(cmd, f"シーン結合 ({n}本)")

    def add_bgm(self, video_path: Path, bgm_path: Path, output_path: Path) -> bool:
        """BGMを追加（動画の音声と混合）"""
        if not bgm_path.exists():
            logger.info("BGMファイルなし、スキップ")
            cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]
            return self._run_ffmpeg(cmd, "BGMなしコピー")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(bgm_path),
            "-filter_complex", "[1:a]volume=0.2[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        return self._run_ffmpeg(cmd, "BGM追加")

    def run(self, generate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        シーン素材を受け取り、最終動画を生成します。

        Args:
            generate_data: Agent 3の出力データ

        Returns:
            dict: 最終動画のパスを含むデータ
        """
        logger.info("=== Agent 4: 動画編集開始 ===")

        date = generate_data.get("date", datetime.now().strftime("%Y%m%d"))
        scene_assets = generate_data.get("scene_assets", [])
        scene_dir = Path(generate_data.get("scene_dir", self.temp_dir))

        if not scene_assets:
            raise ValueError("シーン素材データがありません")

        processed_scene_paths = []

        # ===== 1. 各シーンを処理 =====
        for asset in scene_assets:
            scene_id = asset["scene_id"]
            duration = asset["duration_sec"]
            video_path = Path(asset["video_path"]) if asset.get("video_path") else None
            audio_path = Path(asset["audio_path"]) if asset.get("audio_path") else None
            srt_path = Path(asset["srt_path"]) if asset.get("srt_path") else None

            # ステップ1: 動画を正規化
            normalized_path = scene_dir / f"scene_{scene_id}_normalized.mp4"
            self.normalize_video(video_path, normalized_path, duration)

            # ステップ2: 音声を結合
            merged_path = scene_dir / f"scene_{scene_id}_merged.mp4"
            self.merge_audio_video(normalized_path, audio_path, merged_path, duration)

            # ステップ3: 字幕を焼き込み
            subtitled_path = scene_dir / f"scene_{scene_id}_subtitled.mp4"
            self.burn_subtitles(merged_path, srt_path, subtitled_path)

            processed_scene_paths.append(subtitled_path)
            logger.info(f"シーン {scene_id} 処理完了")

        # ===== 2. シーンを結合 =====
        concat_path = scene_dir / f"concat_{date}.mp4"
        self.concatenate_scenes(processed_scene_paths, concat_path)

        # ===== 3. BGMを追加 =====
        final_path = self.output_dir / f"final_{date}.mp4"
        self.add_bgm(concat_path, config.BGM_PATH, final_path)

        result = {
            "title": generate_data.get("title", ""),
            "description": generate_data.get("description", ""),
            "hashtags": generate_data.get("hashtags", []),
            "thumbnail_text": generate_data.get("thumbnail_text", ""),
            "final_video_path": str(final_path),
            "date": date,
        }

        logger.info(f"Agent 4 完了: {final_path}")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Agent 4 (動画編集) は他のエージェントの出力が必要です。main.py から実行してください。")
