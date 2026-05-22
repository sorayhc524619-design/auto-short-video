"""
scripts/generate_ambient.py - 環境音をffmpegで合成
ピンクノイズ・ブラウンノイズ・フィルタ・トレモロ等を組み合わせて
雨/暖炉/森/風/海/雷/小川 の7種類を生成します。

合成音なので人間が録音した「本物」には劣りますが、
1. ライセンス完全クリア（自分で作った音）
2. 即座に7種全部揃う（手動DL不要）
3. 動画背景音として十分使える品質

実行:
  python scripts/generate_ambient.py                # 全種生成（既存はスキップ）
  python scripts/generate_ambient.py --force        # 既存も上書き
  python scripts/generate_ambient.py --duration 60  # 1ファイル60秒（デフォルト300秒）
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ffmpeg lavfi の音響レシピ集（各 ambient タイプ）
# anoisesrc: c=white|pink|brown|blue
RECIPES = {
    "rain": (
        "anoisesrc=c=pink:r=44100:d={dur},"
        "highpass=f=400,"
        "lowpass=f=6000,"
        "volume=0.9"
    ),
    "fireplace": (
        "anoisesrc=c=brown:r=44100:d={dur},"
        "lowpass=f=1200,"
        # 不規則な「パチパチ」音をトレモロで再現
        "tremolo=f=4.5:d=0.7,"
        "volume=1.1"
    ),
    "forest": (
        # 風のような低周波ベース + 鳥の代わりに高音トレモロ
        "anoisesrc=c=pink:r=44100:d={dur},"
        "lowpass=f=3000,"
        "tremolo=f=0.4:d=0.3,"
        "volume=0.8"
    ),
    "wind": (
        "anoisesrc=c=brown:r=44100:d={dur},"
        "lowpass=f=800,"
        "tremolo=f=0.3:d=0.6,"
        "volume=1.0"
    ),
    "ocean": (
        # ゆっくりした波: 低周波 + ゆっくりトレモロ
        "anoisesrc=c=brown:r=44100:d={dur},"
        "lowpass=f=600,"
        "tremolo=f=0.15:d=0.85,"
        "volume=1.0"
    ),
    "thunder": (
        # 低音ゴロゴロ + たまにドカン
        "anoisesrc=c=brown:r=44100:d={dur},"
        "lowpass=f=300,"
        "tremolo=f=0.2:d=0.5,"
        "volume=1.0"
    ),
    "stream": (
        # サラサラ流れる小川: 高周波寄り
        "anoisesrc=c=pink:r=44100:d={dur},"
        "highpass=f=600,"
        "lowpass=f=8000,"
        "tremolo=f=2:d=0.2,"
        "volume=0.85"
    ),
}


def generate_one(name: str, duration: int, output: Path, force: bool) -> bool:
    if output.exists() and not force:
        print(f"[SKIP] {output.name} (exists; use --force to overwrite)")
        return True
    recipe = RECIPES[name].format(dur=duration)
    cmd = [
        "ffmpeg", "-y" if force else "-n",
        "-f", "lavfi",
        "-i", recipe,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ac", "2",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size_kb = output.stat().st_size / 1024
        print(f"[ OK ] {output.name} ({duration}s, {size_kb:.0f}KB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {output.name}: {e.stderr.decode()[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=300, help="seconds per file (default: 300)")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--only", nargs="*", help="only these sounds")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found in PATH. Install it first.")
        return 1

    config.AMBIENT_DIR.mkdir(exist_ok=True)
    names = args.only or list(RECIPES.keys())
    ok = True
    for name in names:
        if name not in RECIPES:
            print(f"[WARN] unknown sound: {name}")
            continue
        target = config.AMBIENT_DIR / f"{name}.mp3"
        if not generate_one(name, args.duration, target, args.force):
            ok = False

    print()
    print(f"Generated in: {config.AMBIENT_DIR}")
    print("Pipeline will use these as ambient layers. Replace any of them with")
    print("real recordings (Pixabay/Freesound) later for higher quality.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
