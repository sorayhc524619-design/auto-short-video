"""
main.py - パイプラインオーケストレーター
アメリカ向け Cinematic Sleep Music YouTube チャンネルの動画を
自動生成・アップロードします。

実行例:
  python main.py                      # 通常実行
  python main.py --dry-run            # アップロードせず動画生成のみ
  python main.py --duration 600       # 10分尺でテスト
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import config


def setup_logging():
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


logger = logging.getLogger(__name__)


def run_pipeline(dry_run: bool = False, duration_sec: int = None) -> dict:
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("BGM YouTube パイプライン開始")
    logger.info(f"  niche    : {config.CHANNEL_NICHE}")
    logger.info(f"  duration : {duration_sec or config.VIDEO_DURATION_SEC}s")
    logger.info(f"  dry_run  : {dry_run}")
    logger.info("=" * 60)

    if duration_sec:
        config.VIDEO_DURATION_SEC = duration_sec

    for w in config.validate_config():
        logger.warning(f"setup警告: {w}")

    results = {}
    try:
        from agents.agent1_theme import ThemeAgent
        logger.info("\n[1/5] テーマ生成 (Claude)")
        theme = ThemeAgent().run()
        results["theme"] = {
            "name": theme.get("theme_name"),
            "title": theme.get("english_title"),
            "ambient": theme.get("ambient_sound"),
        }

        from agents.agent2_music import MusicAgent
        logger.info("\n[2/5] 音楽生成 (Suno)")
        music_data = MusicAgent().run(theme)
        results["music"] = {"tracks": len(music_data.get("music_tracks", []))}

        from agents.agent3_visual import VisualAgent
        logger.info("\n[3/5] ビジュアル生成 (Stability + Ken Burns)")
        visual_data = VisualAgent().run(music_data)
        results["visual"] = {
            "images": len(visual_data.get("image_paths", [])),
            "loop_base": visual_data.get("loop_base_video"),
        }

        from agents.agent4_compose import ComposeAgent
        logger.info("\n[4/5] コンポジション (ffmpeg)")
        composed = ComposeAgent().run(visual_data)
        results["compose"] = {"final_video": composed.get("final_video_path")}

        if dry_run:
            logger.info("\n[5/5] アップロード (skipped: dry_run)")
            results["upload"] = {"dry_run": True, "video_path": composed.get("final_video_path")}
        else:
            from agents.agent5_upload import UploadAgent
            logger.info("\n[5/5] YouTube アップロード")
            upload = UploadAgent().run(composed)
            results["upload"] = upload

    except Exception as e:
        logger.error(f"パイプライン失敗: {e}", exc_info=True)
        results["error"] = str(e)
        raise
    finally:
        elapsed = (datetime.now() - start).total_seconds()
        results["elapsed_seconds"] = elapsed
        results["timestamp"] = start.isoformat()
        log_path = config.LOG_DIR / f"result_{start.strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        logger.info("=" * 60)
        logger.info(f"完了 ({elapsed:.1f}s) / log: {log_path}")
        logger.info("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="BGM YouTube 自動生成・投稿パイプライン")
    parser.add_argument("--dry-run", action="store_true", help="アップロードせず生成のみ")
    parser.add_argument("--duration", type=int, help="動画尺（秒）。テスト用に短縮する場合に指定")
    parser.add_argument("--mock", action="store_true",
                        help="モックモード: Claude/Suno/Stability を呼ばずffmpeg合成素材で全段テスト")
    parser.add_argument("--local-music", type=str, default="",
                        help="MP3/WAVを置いたローカルディレクトリ。指定するとSuno APIを呼ばない")
    parser.add_argument("--local-image", type=str, default="",
                        help="ローカル画像ファイル or ディレクトリ。指定するとStability APIを呼ばない")
    args = parser.parse_args()
    if args.mock:
        config.MOCK_MODE = True
        os.environ["MOCK_MODE"] = "true"
    if args.local_music:
        config.LOCAL_MUSIC_DIR = args.local_music
        os.environ["LOCAL_MUSIC_DIR"] = args.local_music
    if args.local_image:
        config.LOCAL_IMAGE_PATH = args.local_image
        os.environ["LOCAL_IMAGE_PATH"] = args.local_image
    setup_logging()
    run_pipeline(dry_run=args.dry_run or args.mock, duration_sec=args.duration)


if __name__ == "__main__":
    main()
