"""
agent4_compose.py - Agent 4: 動画コンポジション
- 複数の音楽トラックをクロスフェードで連結 → 目標尺までループ
- 環境音（雨・暖炉等）を低音量でミックス
- ループ基礎動画を目標尺まで繰り返し
- タイトルカード（イントロ6秒）を頭につける
- 最終 mp4 を output/ に出力
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def run_ffmpeg(cmd: List[str], desc: str) -> bool:
    logger.info(f"ffmpeg: {desc}")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg失敗 ({desc}): {e.stderr.decode()[:1000]}")
        raise


def crossfade_concat_audio(tracks: List[Path], output_path: Path, crossfade_sec: int) -> Path:
    """音楽トラックをクロスフェードで連結"""
    if len(tracks) == 1:
        cmd = ["ffmpeg", "-y", "-i", str(tracks[0]), "-c:a", "libmp3lame", str(output_path)]
        run_ffmpeg(cmd, "single track copy")
        return output_path

    inputs = []
    for t in tracks:
        inputs += ["-i", str(t)]

    # acrossfade を逐次適用
    # [0:a][1:a]acrossfade=d=X[a01]; [a01][2:a]acrossfade=d=X[a012]; ...
    filters = []
    prev_label = "0:a"
    for i in range(1, len(tracks)):
        out_label = f"a{i}"
        filters.append(
            f"[{prev_label}][{i}:a]acrossfade=d={crossfade_sec}:c1=tri:c2=tri[{out_label}]"
        )
        prev_label = out_label

    filter_complex = ";".join(filters)
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev_label}]",
        "-c:a", "libmp3lame",
        "-b:a", config.AUDIO_BITRATE,
        str(output_path),
    ]
    run_ffmpeg(cmd, f"crossfade {len(tracks)} tracks")
    return output_path


def loop_audio_to_duration(input_audio: Path, output_path: Path, target_sec: int) -> Path:
    """音声を target_sec までループ"""
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(input_audio),
        "-t", str(target_sec),
        "-c:a", "libmp3lame",
        "-b:a", config.AUDIO_BITRATE,
        str(output_path),
    ]
    run_ffmpeg(cmd, f"loop audio to {target_sec}s")
    return output_path


def mix_with_ambient(music_path: Path, ambient_path: Optional[Path], output_path: Path, target_sec: int) -> Path:
    """音楽と環境音を低音量でミックス"""
    if not ambient_path or not ambient_path.exists():
        if ambient_path:
            logger.warning(f"環境音ファイルなし: {ambient_path}（音楽のみで続行）")
        # 音楽のみ → 音量調整してコピー
        cmd = [
            "ffmpeg", "-y",
            "-i", str(music_path),
            "-af", f"volume={config.MUSIC_VOLUME}",
            "-t", str(target_sec),
            "-c:a", "libmp3lame",
            "-b:a", config.AUDIO_BITRATE,
            str(output_path),
        ]
        run_ffmpeg(cmd, "music only (no ambient)")
        return output_path

    cmd = [
        "ffmpeg", "-y",
        "-i", str(music_path),
        "-stream_loop", "-1", "-i", str(ambient_path),
        "-filter_complex", (
            f"[0:a]volume={config.MUSIC_VOLUME}[m];"
            f"[1:a]volume={config.AMBIENT_VOLUME}[a];"
            f"[m][a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]"
        ),
        "-map", "[out]",
        "-t", str(target_sec),
        "-c:a", "libmp3lame",
        "-b:a", config.AUDIO_BITRATE,
        str(output_path),
    ]
    run_ffmpeg(cmd, "mix music + ambient")
    return output_path


def loop_video_to_duration(input_video: Path, output_path: Path, target_sec: int) -> Path:
    """映像を target_sec までループ（再エンコードあり）"""
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(input_video),
        "-t", str(target_sec),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-r", str(config.VIDEO_FPS),
        "-an",
        str(output_path),
    ]
    run_ffmpeg(cmd, f"loop video to {target_sec}s")
    return output_path


def _ffmpeg_escape_path(p: str) -> str:
    """ffmpeg drawtext filter 用にパスをエスケープ（Windowsの C: 対策）"""
    return p.replace("\\", "/").replace(":", r"\:")


def make_title_card(title_text: str, output_path: Path, duration_sec: int) -> Path:
    """シンプルなタイトルカード（暗背景＋テキスト）"""
    safe = title_text.replace("'", "").replace(":", "")[:80]
    font = _ffmpeg_escape_path(config.FONT_PATH)
    vf = (
        f"drawtext=fontfile={font}:text='{safe}':"
        f"fontsize={config.TITLE_FONT_SIZE}:fontcolor=white:"
        f"x=(w-tw)/2:y=(h-th)/2:"
        f"alpha='if(lt(t,1),t,if(lt(t,{duration_sec-1}),1,{duration_sec}-t))'"
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0a14:size={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:duration={duration_sec}:r={config.VIDEO_FPS}",
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        str(output_path),
    ]
    run_ffmpeg(cmd, "title card")
    return output_path


def concat_video_segments(segments: List[Path], output_path: Path) -> Path:
    """連結（同フォーマット前提で concat demuxer）"""
    work = output_path.parent
    list_file = work / "video_concat.txt"
    with open(list_file, "w") as f:
        for s in segments:
            f.write(f"file '{s.resolve()}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path),
    ]
    run_ffmpeg(cmd, "concat video segments")
    return output_path


def mux_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", config.AUDIO_BITRATE,
        "-shortest",
        str(output_path),
    ]
    run_ffmpeg(cmd, "mux v+a")
    return output_path


class ComposeAgent:
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("=== Agent 4: コンポジション開始 ===")
        date = data.get("date")
        theme_name = data.get("theme_name", "untitled")
        work_dir = config.TEMP_DIR / f"{date}_{theme_name}" / "compose"
        work_dir.mkdir(parents=True, exist_ok=True)

        target_sec = config.VIDEO_DURATION_SEC
        title_sec = config.TITLE_CARD_DURATION_SEC
        loop_sec = target_sec - title_sec  # タイトル分を差し引く

        tracks = [Path(p) for p in data.get("music_tracks", [])]
        if not tracks:
            raise ValueError("music_tracks がありません")

        # ===== 1. 音楽: クロスフェード結合 → ループ =====
        crossfaded = work_dir / "crossfaded.mp3"
        crossfade_concat_audio(tracks, crossfaded, config.MUSIC_CROSSFADE_SEC)

        looped_music = work_dir / "music_looped.mp3"
        loop_audio_to_duration(crossfaded, looped_music, loop_sec)

        # ===== 2. 環境音ミックス =====
        ambient_key = data.get("ambient_sound", "none")
        ambient_path = config.AMBIENT_FILES.get(ambient_key)
        final_audio = work_dir / "final_audio.mp3"
        mix_with_ambient(looped_music, ambient_path, final_audio, loop_sec)

        # ===== 3. 映像: ループ =====
        loop_base = Path(data["loop_base_video"])
        looped_video = work_dir / "video_looped.mp4"
        loop_video_to_duration(loop_base, looped_video, loop_sec)

        # ===== 4. タイトルカード =====
        title_card = work_dir / "title_card.mp4"
        make_title_card(data.get("thumbnail_text") or data.get("english_title", ""), title_card, title_sec)

        # ===== 5. 映像連結（タイトル + 本編） =====
        full_video = work_dir / "video_full.mp4"
        concat_video_segments([title_card, looped_video], full_video)

        # ===== 6. 音声側にも先頭の無音(タイトル分)をパディング =====
        padded_audio = work_dir / "audio_padded.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-t", str(title_sec), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-i", str(final_audio),
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", config.AUDIO_BITRATE,
            str(padded_audio),
        ]
        run_ffmpeg(cmd, "audio padding for title card")

        # ===== 7. mux =====
        final_path = config.OUTPUT_DIR / f"final_{date}_{theme_name}.mp4"
        mux_video_audio(full_video, padded_audio, final_path)

        result = dict(data)
        result["final_video_path"] = str(final_path)
        logger.info(f"Agent 4 完了: {final_path}")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Agent 4 は前段の出力が必要です。main.py から実行してください。")
