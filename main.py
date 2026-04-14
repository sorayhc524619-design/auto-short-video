"""
main.py - パイプラインオーケストレーター
5つのエージェントを順番に起動し、ショート動画の自動生成・投稿を実行します。

実行方法:
  python main.py
  python main.py --genre "テクノロジー"
  python main.py --dry-run  # 投稿せずに動画のみ生成
"""

import asyncio
import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

import config

# ロギング設定
def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format=log_format,
        handlers=handlers,
    )

logger = logging.getLogger(__name__)


async def run_pipeline(genre: str = None, dry_run: bool = False):
    """
    全パイプラインを実行します。

    Args:
        genre: コンテンツジャンル（Noneの場合はconfig.CONTENT_GENREを使用）
        dry_run: Trueの場合は投稿せずに動画のみ生成
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 ショート動画自動生成パイプライン 開始")
    logger.info(f"   日時: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   ジャンル: {genre or config.CONTENT_GENRE}")
    logger.info(f"   ドライラン: {dry_run}")
    logger.info("=" * 60)

    # ジャンル設定
    if genre:
        config.CONTENT_GENRE = genre

    # 設定チェック
    warnings = config.validate_config()
    for w in warnings:
        logger.warning(f"設定警告: {w}")

    results = {}

    try:
        # ===== Agent 1: トレンド取得 =====
        from agents.agent1_trends import TrendAgent
        logger.info("\n📡 Agent 1: トレンド取得")
        agent1 = TrendAgent()
        trend_data = agent1.run()
        results["trends"] = trend_data
        logger.info(f"✅ トレンド取得完了: {trend_data['keywords']}")

        # ===== Agent 2: スクリプト生成 =====
        from agents.agent2_script import ScriptAgent
        logger.info("\n✍️ Agent 2: スクリプト生成")
        agent2 = ScriptAgent()
        script_data = agent2.run(trend_data)
        results["script"] = {
            "title": script_data.get("title"),
            "scenes_count": len(script_data.get("scenes", [])),
        }
        logger.info(f"✅ スクリプト生成完了: 「{script_data.get('title')}」")

        # ===== Agent 3: 並列生成 =====
        from agents.agent3_generate import GenerateAgent
        logger.info("\n🎬 Agent 3: 音声・映像・字幕 並列生成")
        agent3 = GenerateAgent()
        generate_data = await agent3.run(script_data)
        results["generate"] = {
            "scene_assets_count": len(generate_data.get("scene_assets", [])),
        }
        logger.info(f"✅ 素材生成完了: {len(generate_data['scene_assets'])}シーン")

        # ===== Agent 4: 動画編集 =====
        from agents.agent4_edit import EditAgent
        logger.info("\n✂️ Agent 4: 動画編集・合成")
        agent4 = EditAgent()
        edit_data = agent4.run(generate_data)
        results["edit"] = {
            "final_video_path": edit_data.get("final_video_path"),
        }
        logger.info(f"✅ 動画編集完了: {edit_data.get('final_video_path')}")

        # ===== Agent 5: 自動投稿 =====
        if dry_run:
            logger.info("\n⏭️ Agent 5: 自動投稿（ドライランのためスキップ）")
            results["post"] = {"dry_run": True, "video_path": edit_data.get("final_video_path")}
        else:
            from agents.agent5_post import PostAgent
            logger.info("\n📤 Agent 5: 自動投稿")
            agent5 = PostAgent()
            post_data = agent5.run(edit_data)
            results["post"] = post_data
            logger.info(f"✅ 投稿完了: YouTube={post_data.get('youtube')}, TikTok={post_data.get('tiktok')}")

    except Exception as e:
        logger.error(f"❌ パイプライン失敗: {e}", exc_info=True)
        results["error"] = str(e)
        raise

    finally:
        # 実行結果をJSONで保存
        elapsed = (datetime.now() - start_time).total_seconds()
        results["elapsed_seconds"] = elapsed
        results["timestamp"] = start_time.isoformat()

        result_path = config.LOG_DIR / f"result_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        logger.info("\n" + "=" * 60)
        logger.info(f"🏁 パイプライン完了 ({elapsed:.1f}秒)")
        logger.info(f"📄 実行ログ: {result_path}")
        logger.info("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="ショート動画自動生成・投稿パイプライン")
    parser.add_argument("--genre", type=str, help="コンテンツジャンル（例: テクノロジー）")
    parser.add_argument("--dry-run", action="store_true", help="動画生成のみ（投稿しない）")
    args = parser.parse_args()

    setup_logging()
    asyncio.run(run_pipeline(genre=args.genre, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
