"""
bgm_pipeline.py - Suno AI製BGMの長尺動画 自動生成・YouTube自動投稿パイプライン

Sunoで生成したMP3を bgm_input/ に置いて実行すると、以下を全自動で行います:
  1. 楽曲をフェード処理＆ラウドネス正規化して指定時間（例: 1時間）のミックスを作成
  2. 背景画像を生成（Stability AI、なければグラデーション画像）し、
     ゆっくりズームする動きのある映像ループを作成（静止画一枚のみの動画は
     YouTubeの「再利用コンテンツ」扱いになるため）
  3. タイムスタンプ付きトラックリスト（チャプター）を含む英語のタイトル・
     説明文・タグをClaude APIで生成
  4. サムネイルを生成してYouTubeへアップロード

実行方法:
  python bgm_pipeline.py --niche rain_sleep --hours 1 --dry-run   # 動画生成のみ
  python bgm_pipeline.py --niche rain_sleep --hours 1             # 生成+投稿
  python bgm_pipeline.py --list-niches                            # ニッチ一覧
"""

import argparse
import json
import logging
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import config
from bgm.niches import NICHES, DEFAULT_NICHE

logger = logging.getLogger(__name__)

INPUT_DIR = config.BASE_DIR / "bgm_input"
BACKGROUND_DIR = config.BASE_DIR / "bgm_background"
BGM_OUTPUT_DIR = config.OUTPUT_DIR / "bgm"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
LOOP_SECONDS = 60  # ズームループ1周期の長さ（ピンポンズームで継ぎ目なし）

BGM_CLAUDE_MODEL = "claude-opus-4-8"


def run_ffmpeg(args: list, desc: str):
    """ffmpeg/ffprobeコマンドを実行し、失敗時はstderrを添えて例外を投げます"""
    logger.debug(f"実行: {' '.join(str(a) for a in args)}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{desc} 失敗:\n{result.stderr[-2000:]}")
    return result


def probe_duration(path: Path) -> float:
    """ffprobeで音声/動画ファイルの長さ（秒）を取得します"""
    result = run_ffmpeg([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], f"ffprobe ({path.name})")
    return float(result.stdout.strip())


# ===== Step 1: 音声ミックス作成 =====

def collect_tracks(input_dir: Path) -> list:
    """入力フォルダからSunoの楽曲ファイルを集めます"""
    exts = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
    tracks = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in exts)
    if not tracks:
        raise FileNotFoundError(
            f"{input_dir} に楽曲ファイルがありません。"
            "SunoでダウンロードしたMP3を置いてください。"
        )
    return tracks


def track_title(path: Path) -> str:
    """ファイル名から表示用のトラック名を作ります（先頭の番号と末尾の(1)等を除去）"""
    name = re.sub(r"^\d+[\s._-]*", "", path.stem)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    return name.replace("_", " ").strip().title() or path.stem


def dedupe_titles(titles: list) -> list:
    """同名トラック（Sunoの別テイク）にII, III...を付けて区別します"""
    romans = ["", " II", " III", " IV", " V", " VI"]
    seen = {}
    result = []
    for t in titles:
        seen[t] = seen.get(t, 0) + 1
        n = seen[t]
        result.append(f"{t}{romans[n-1]}" if n <= len(romans) else f"{t} ({n})")
    return result


def build_audio_mix(tracks: list, target_hours: float, work_dir: Path):
    """
    各トラックにフェードイン/アウトとラウドネス正規化をかけ、
    シャッフル＆リピートして目標時間のミックスを作成します。

    Returns:
        (ミックスファイルのPath, [(開始秒, トラック名), ...])
    """
    target_sec = target_hours * 3600
    norm_dir = work_dir / "normalized"
    norm_dir.mkdir(exist_ok=True)

    normalized = []  # (path, duration, title)
    for i, track in enumerate(tracks):
        dur = probe_duration(track)
        out = norm_dir / f"track_{i:02d}.m4a"
        fade_out_start = max(dur - 3, 0)
        run_ffmpeg([
            "ffmpeg", "-y", "-i", str(track),
            "-vn",  # SunoのMP3に埋め込まれたカバー画像を無視
            "-af",
            f"afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.2f}:d=3,"
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
            str(out),
        ], f"トラック正規化 ({track.name})")
        normalized.append((out, probe_duration(out), track_title(track)))
        logger.info(f"  ♪ {track.name} ({dur:.0f}秒) を処理しました")

    titles = dedupe_titles([t for _, _, t in normalized])
    normalized = [(p, d, t) for (p, d, _), t in zip(normalized, titles)]

    # シャッフルしながら目標時間までプレイリストを構築
    playlist = []
    total = 0.0
    rng = random.Random(42)  # 再現性のため固定シード
    while total < target_sec:
        order = normalized[:]
        rng.shuffle(order)
        for item in order:
            playlist.append(item)
            total += item[1]
            if total >= target_sec:
                break

    # トラックリスト（チャプター用タイムスタンプ）
    tracklist = []
    t = 0.0
    for _, dur, title in playlist:
        tracklist.append((t, title))
        t += dur

    # concat demuxerで結合（全トラック同一コーデックなので再エンコード不要）
    list_file = work_dir / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for path, _, _ in playlist:
            f.write(f"file '{path.resolve()}'\n")

    mix_path = work_dir / "mix.m4a"
    run_ffmpeg([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy", str(mix_path),
    ], "音声ミックス結合")

    logger.info(f"  🎧 ミックス完成: {total/3600:.2f}時間 / {len(playlist)}トラック")
    return mix_path, tracklist


# ===== Step 2: 背景映像作成 =====

def find_background_video(niche_key: str) -> Path:
    """
    bgm_background/ から背景用の動画を探します。
    ニッチ名と同名のファイル（例: rain_sleep.mp4）があれば優先、
    なければ最初に見つかった動画を使います。見つからなければNone。
    """
    if not BACKGROUND_DIR.exists():
        return None
    exts = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
    videos = sorted(p for p in BACKGROUND_DIR.iterdir() if p.suffix.lower() in exts)
    if not videos:
        return None
    for v in videos:
        if v.stem.lower() == niche_key:
            return v
    return videos[0]


def prepare_background_video(video_path: Path, work_dir: Path):
    """
    背景動画を1080p/30fpsに揃えてループ用に変換し、
    サムネイル用に1フレーム切り出します。

    Returns:
        (ループ動画のPath, サムネイル用画像のPath)
    """
    loop_path = work_dir / "motion_loop.mp4"
    run_ffmpeg([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf",
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},fps={VIDEO_FPS},format=yuv420p",
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        str(loop_path),
    ], f"背景動画の変換 ({video_path.name})")

    image_path = work_dir / "background.png"
    run_ffmpeg([
        "ffmpeg", "-y", "-ss", "1", "-i", str(loop_path),
        "-frames:v", "1", str(image_path),
    ], "サムネイル用フレーム抽出")

    dur = probe_duration(loop_path)
    logger.info(f"  🎞️ 背景動画を使用: {video_path.name} ({dur:.0f}秒ループ)")
    return loop_path, image_path


def generate_background_image(niche: dict, work_dir: Path) -> Path:
    """Stability AIで背景画像を生成。APIキーがなければグラデーション画像を作ります"""
    image_path = work_dir / "background.png"

    if config.STABILITY_API_KEY:
        try:
            import requests
            logger.info("  🎨 Stability AIで背景画像を生成中...")
            resp = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "Authorization": f"Bearer {config.STABILITY_API_KEY}",
                    "Accept": "image/*",
                },
                files={"none": ""},
                data={
                    "prompt": niche["visual_prompt"],
                    "output_format": "png",
                    "aspect_ratio": "16:9",
                },
                timeout=120,
            )
            resp.raise_for_status()
            image_path.write_bytes(resp.content)
            return image_path
        except Exception as e:
            logger.warning(f"  画像生成APIが失敗したためグラデーションで代替します: {e}")

    # フォールバック: 縦グラデーション + ボケ光（夜の街明かり風）
    # 模様のない単色グラデーションだとズームしても動きが見えないため、
    # 光の粒を散らしてカメラの動きがわかるようにする
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    import numpy as np

    (r1, g1, b1), (r2, g2, b2) = niche["fallback_colors"]
    h, w = VIDEO_HEIGHT, VIDEO_WIDTH
    grad = np.linspace(0, 1, h).reshape(h, 1, 1)
    top = np.array([r1, g1, b1]).reshape(1, 1, 3)
    bottom = np.array([r2, g2, b2]).reshape(1, 1, 3)
    img_arr = top + (bottom - top) * grad
    noise = np.random.default_rng(0).normal(0, 4, (h, w, 3))
    img = Image.fromarray(np.clip(img_arr + noise, 0, 255).astype("uint8"))

    rng = random.Random(7)
    glow_color = (
        min(int(r2 * 1.9 + 40), 255),
        min(int(g2 * 1.9 + 40), 255),
        min(int(b2 * 1.7 + 30), 255),
    )
    bokeh = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(bokeh)
    for _ in range(60):
        x = rng.randint(0, w)
        y = rng.randint(int(h * 0.25), h)
        r = rng.randint(8, 70)
        brightness = rng.uniform(0.25, 1.0)
        c = tuple(int(v * brightness) for v in glow_color)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=c)
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(22))
    img = ImageChops.screen(img, bokeh)

    img.save(image_path)
    logger.info("  🎨 ボケ光入りグラデーション背景を生成しました")
    return image_path


def build_motion_loop(image_path: Path, work_dir: Path) -> Path:
    """
    背景画像からゆっくりズームイン/アウトする映像ループを作成します。
    cos波でズームするため、ループの継ぎ目が目立ちません。
    """
    loop_path = work_dir / "motion_loop.mp4"
    frames = LOOP_SECONDS * VIDEO_FPS
    # 事前に拡大してからzoompanをかけるとジッターが減る
    # ズーム(1.0〜1.24)と横揺れを同じ周期にすることで継ぎ目のないループになる
    zoom_expr = f"1.12-0.12*cos(2*PI*on/{frames})"
    pan_x = f"(iw-iw/zoom)/2*(1+0.7*sin(2*PI*on/{frames}))"
    run_ffmpeg([
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
        "-vf",
        f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
        f"zoompan=z='{zoom_expr}':x='{pan_x}':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:fps={VIDEO_FPS}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT},format=yuv420p",
        "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        str(loop_path),
    ], "映像ループ生成")
    logger.info(f"  🎞️ {LOOP_SECONDS}秒の映像ループを生成しました")
    return loop_path


def build_final_video(loop_path: Path, mix_path: Path, out_path: Path) -> Path:
    """映像ループを音声の長さだけ繰り返して最終動画を作成します（再エンコードなし）"""
    run_ffmpeg([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(loop_path),
        "-i", str(mix_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "copy",
        "-shortest", "-movflags", "+faststart",
        str(out_path),
    ], "最終動画合成")
    logger.info(f"  ✅ 最終動画: {out_path} ({out_path.stat().st_size/1e6:.0f}MB)")
    return out_path


def make_thumbnail(image_path: Path, title_text: str, work_dir: Path) -> Path:
    """背景画像にタイトル文字を載せたサムネイル(1280x720)を作成します"""
    from PIL import Image, ImageDraw, ImageFont

    thumb_path = work_dir / "thumbnail.jpg"
    img = Image.open(image_path).convert("RGB").resize((1280, 720))
    draw = ImageDraw.Draw(img, "RGBA")

    font = None
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, 88)
            break
    if font is None:
        font = ImageFont.load_default()

    # 下部に半透明の帯 + 白文字（2行まで）
    words = title_text.split()
    lines, line = [], ""
    for w in words:
        if draw.textlength(f"{line} {w}".strip(), font=font) > 1180:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    lines.append(line)
    lines = lines[:2]

    band_h = 60 + 100 * len(lines)
    draw.rectangle([(0, 720 - band_h), (1280, 720)], fill=(0, 0, 0, 160))
    y = 720 - band_h + 30
    for ln in lines:
        draw.text((50, y), ln, font=font, fill="white",
                  stroke_width=3, stroke_fill="black")
        y += 100

    img.save(thumb_path, quality=92)
    logger.info(f"  🖼️ サムネイル: {thumb_path}")
    return thumb_path


# ===== Step 3: メタデータ生成 =====

def format_timestamp(sec: float) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def build_tracklist_text(tracklist: list) -> str:
    return "\n".join(f"{format_timestamp(t)} {title}" for t, title in tracklist)


def generate_metadata(niche: dict, hours: float, tracklist: list) -> dict:
    """Claude APIで英語のタイトル・説明文・タグを生成。失敗時はテンプレートで代替"""
    hours_label = "1 Hour" if hours == 1 else f"{hours:g} Hours"
    fallback = {
        "title": niche["title_templates"][0].format(hours=hours_label),
        "description": niche["description_intro"],
        "tags": niche["tags"],
    }

    if not config.CLAUDE_API_KEY:
        logger.warning("  CLAUDE_API_KEY未設定のためテンプレートのメタデータを使用します")
        meta = fallback
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
            prompt = f"""You are a YouTube growth expert for US-audience ambient/BGM music channels.
Generate metadata for a "{niche['display_name']}" video ({hours_label} long).

Reference title styles: {json.dumps(niche['title_templates'])}
Reference description intro: {niche['description_intro']}

Return ONLY a JSON object with this exact shape:
{{
  "title": "compelling SEO title under 100 chars, include the duration ({hours_label}) and 1 fitting emoji",
  "description": "2 short paragraphs: what the music is for (sleep/study/relax keywords US viewers search), and a warm invitation to subscribe for weekly uploads",
  "tags": ["12-15 search tags US viewers actually use"]
}}"""
            response = client.messages.create(
                model=BGM_CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            meta = json.loads(match.group(0))
            logger.info("  📝 Claudeでメタデータを生成しました")
        except Exception as e:
            logger.warning(f"  メタデータ生成に失敗したためテンプレートを使用します: {e}")
            meta = fallback

    # チャプター（トラックリスト）とAI開示・クレジットを説明文に追加
    meta["description"] = (
        f"{meta['description']}\n\n"
        f"🎵 Tracklist:\n{build_tracklist_text(tracklist)}\n\n"
        "All music on this channel is original, created and curated by us "
        "(composed with the assistance of AI tools, then selected, arranged and "
        "mastered by a human). Visuals are original.\n"
        "© All rights reserved. Please do not re-upload."
    )
    meta["title"] = meta["title"][:100]
    return meta


# ===== Step 4: YouTubeアップロード =====

def upload_to_youtube(video_path: Path, thumb_path: Path, meta: dict) -> str:
    """長尺BGM動画をYouTubeにアップロードします（カテゴリ: 音楽 / 言語: 英語）"""
    if not config.YOUTUBE_CREDENTIALS_JSON:
        logger.warning("YOUTUBE_CREDENTIALS_JSON が未設定 → アップロードをスキップ")
        return None

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds_data = json.loads(config.YOUTUBE_CREDENTIALS_JSON)
    credentials = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        scopes=creds_data.get("scopes", ["https://www.googleapis.com/auth/youtube.upload"]),
    )
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"][:5000],
            "tags": meta["tags"],
            "categoryId": "10",  # Music
            "defaultLanguage": "en",
            "defaultAudioLanguage": "zxx",  # 歌詞なし（言語によらない）
        },
        "status": {
            "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,
            "madeForKids": False,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path), mimetype="video/mp4",
        resumable=True, chunksize=1024 * 1024 * 16,
    )
    logger.info(f"YouTube アップロード開始: {meta['title']}")
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media,
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"  アップロード進捗: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    logger.info(f"✅ アップロード成功: https://www.youtube.com/watch?v={video_id}")

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumb_path), mimetype="image/jpeg"),
        ).execute()
        logger.info("  🖼️ サムネイルを設定しました")
    except Exception as e:
        logger.warning(f"  サムネイル設定に失敗（手動で設定してください）: {e}")

    return video_id


# ===== パイプライン本体 =====

def run_pipeline(niche_key: str, hours: float, dry_run: bool, input_dir: Path):
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError("ffmpegが見つかりません。先にインストールしてください。")

    niche = NICHES[niche_key]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = BGM_OUTPUT_DIR / f"{niche_key}_{stamp}"
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info(f"🎵 BGM動画パイプライン開始: {niche['display_name']} / {hours}時間")
    logger.info("=" * 60)

    logger.info("\n[1/4] 音声ミックス作成")
    tracks = collect_tracks(input_dir)
    mix_path, tracklist = build_audio_mix(tracks, hours, work_dir)

    logger.info("\n[2/4] 背景映像作成")
    bg_video = find_background_video(niche_key)
    if bg_video:
        loop_path, image_path = prepare_background_video(bg_video, work_dir)
    else:
        image_path = generate_background_image(niche, work_dir)
        loop_path = build_motion_loop(image_path, work_dir)
    video_path = build_final_video(loop_path, mix_path, work_dir / "final.mp4")

    logger.info("\n[3/4] メタデータ・サムネイル生成")
    meta = generate_metadata(niche, hours, tracklist)
    thumb_path = make_thumbnail(image_path, meta["title"].split("🌧")[0].split("🌌")[0]
                                .split("📚")[0].split("📻")[0].split("🕯")[0]
                                .split("🌙")[0].strip(), work_dir)

    meta_path = work_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    logger.info(f"  📄 メタデータ: {meta_path}")

    logger.info("\n[4/4] YouTubeアップロード")
    video_id = None
    if dry_run:
        logger.info("  ⏭️ ドライランのためスキップ。生成物を確認してください:")
        logger.info(f"     動画: {video_path}")
        logger.info(f"     サムネ: {thumb_path}")
        logger.info(f"     メタデータ: {meta_path}")
    else:
        video_id = upload_to_youtube(video_path, thumb_path, meta)

    logger.info("\n🏁 パイプライン完了")
    return {"video_path": str(video_path), "video_id": video_id, "metadata": meta}


def main():
    parser = argparse.ArgumentParser(description="Suno BGM長尺動画 自動生成・投稿")
    parser.add_argument("--niche", default=DEFAULT_NICHE, choices=list(NICHES.keys()),
                        help="ニッチ（ジャンル）プリセット")
    parser.add_argument("--hours", type=float, default=1.0, help="動画の長さ（時間）")
    parser.add_argument("--dry-run", action="store_true", help="生成のみ（投稿しない）")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR,
                        help="Suno楽曲フォルダ（デフォルト: bgm_input/）")
    parser.add_argument("--list-niches", action="store_true", help="ニッチ一覧とSunoプロンプトを表示")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if args.list_niches:
        for key, n in NICHES.items():
            print(f"\n=== {key}: {n['display_name']} ===")
            print("Sunoプロンプト（Style欄にコピペ）:")
            for p in n["suno_prompts"]:
                print(f"  - {p}")
        return

    run_pipeline(args.niche, args.hours, args.dry_run, args.input_dir)


if __name__ == "__main__":
    main()
