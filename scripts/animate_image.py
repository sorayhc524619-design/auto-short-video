"""
scripts/animate_image.py - 静止画→ループアニメ動画生成

ChatGPT/Stability等で生成した静止画に、ffmpeg で以下の動き効果を付与し、
ループ可能な mp4 を出力する：
  - rain     : 半透明の雨ストリーク（縦に流れる）
  - flicker  : 全体の明度を微妙に揺らす（炎の揺らぎ感）
  - zoom     : ゆっくりズームイン (Ken Burns)
  - grain    : 微細なフィルムグレイン（落ち着き）

実行例:
  python scripts/animate_image.py input.png output.mp4 --duration 60 --effects rain,zoom
  python scripts/animate_image.py input.png output.mp4 --effects rain,flicker,zoom,grain
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


VALID_EFFECTS = {"rain", "flicker", "zoom", "grain"}


def build_filter_complex(
    duration_sec: int,
    fps: int,
    width: int,
    height: int,
    effects: set,
) -> tuple:
    """ffmpeg の filter_complex 文字列と追加入力数を返す"""
    total_frames = duration_sec * fps

    # ベース: 画像をスケール（zoom時は大きめにして余白確保）
    if "zoom" in effects:
        base = (
            f"[0:v]scale={int(width*1.3)}:{int(height*1.3)}:force_original_aspect_ratio=increase,"
            f"crop={int(width*1.3)}:{int(height*1.3)},"
            f"zoompan=z='min(zoom+0.00008,1.12)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps}[bg]"
        )
    else:
        base = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps={fps}[bg]"
        )

    chain = [base]
    last_label = "bg"
    extra_inputs = []  # ['-f', 'lavfi', '-i', ...]

    # flicker: 明度の微妙な揺らぎ
    if "flicker" in effects:
        chain.append(
            f"[{last_label}]eq=brightness='0.02*sin(2*PI*t*0.6)+0.015*sin(2*PI*t*1.7)':"
            f"contrast='1+0.02*sin(2*PI*t*0.8)'[flickered]"
        )
        last_label = "flickered"

    # grain: フィルムグレイン
    if "grain" in effects:
        chain.append(f"[{last_label}]noise=alls=4:allf=t,format=yuv420p[grained]")
        last_label = "grained"

    # rain: 縦に流れる半透明の雨
    if "rain" in effects:
        rain_input_idx = len(extra_inputs) // 4 + 1  # 最初の追加入力
        extra_inputs += ["-f", "lavfi",
                         "-i", f"nullsrc=s={width}x{height}:r={fps}:d={duration_sec}"]
        chain.append(
            f"[{rain_input_idx}:v]format=gray,"
            f"geq=lum_expr='if(lt(random(0)*1000,2),255,0)':a='90',"
            f"boxblur=0.5:0:1:0,"
            f"format=yuva420p[rain]"
        )
        chain.append(f"[{last_label}][rain]overlay=y=0:x=0:format=auto[overlaid]")
        last_label = "overlaid"

    # 最終フォーマット
    chain.append(f"[{last_label}]format=yuv420p[out]")

    return ";".join(chain), extra_inputs


def animate(
    input_path: Path,
    output_path: Path,
    duration_sec: int = 60,
    effects: list = None,
    width: int = None,
    height: int = None,
    fps: int = None,
) -> bool:
    if effects is None:
        effects = ["rain", "zoom"]
    effects_set = set(effects) & VALID_EFFECTS
    if not effects_set:
        logger.warning("有効なエフェクトが指定されていません。zoomだけ適用します")
        effects_set = {"zoom"}

    w = width or config.VIDEO_WIDTH
    h = height or config.VIDEO_HEIGHT
    f = fps or config.VIDEO_FPS

    filter_complex, extra_inputs = build_filter_complex(duration_sec, f, w, h, effects_set)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(input_path),
        *extra_inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-r", str(f),
        str(output_path),
    ]
    logger.info(f"アニメ生成中 (効果: {sorted(effects_set)}, 尺: {duration_sec}s)")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"出力: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg失敗: {e.stderr.decode()[:2000]}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="入力画像（png/jpg/webp）")
    parser.add_argument("output", help="出力動画（mp4）")
    parser.add_argument("--duration", type=int, default=60, help="動画尺（秒）")
    parser.add_argument(
        "--effects", type=str, default="rain,zoom",
        help=f"カンマ区切り。選択肢: {','.join(sorted(VALID_EFFECTS))}",
    )
    args = parser.parse_args()

    effects = [e.strip() for e in args.effects.split(",") if e.strip()]
    ok = animate(
        Path(args.input).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
        duration_sec=args.duration,
        effects=effects,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
