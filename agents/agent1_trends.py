"""
agent1_trends.py - Agent 1: トレンド取得エージェント
Google Trends / RSS フィードから今日のトレンドキーワードを収集します。
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any

import feedparser
import requests
from pytrends.request import TrendReq

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class TrendAgent:
    """トレンドキーワードを収集するエージェント"""

    def __init__(self):
        self.genre = config.CONTENT_GENRE
        self.max_keywords = config.MAX_TREND_KEYWORDS

    def get_google_trends(self) -> List[str]:
        """Google Trendsから日本のトレンドキーワードを取得"""
        try:
            pytrends = TrendReq(hl="ja-JP", tz=540, timeout=(10, 25))
            trending = pytrends.trending_searches(pn="japan")
            keywords = trending[0].tolist()[:self.max_keywords]
            logger.info(f"Google Trends取得成功: {keywords}")
            return keywords
        except Exception as e:
            logger.warning(f"Google Trends取得失敗: {e}")
            return []

    def get_rss_headlines(self) -> List[str]:
        """RSSフィードからヘッドラインを取得"""
        headlines = []
        for feed_url in config.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    headlines.append(entry.title)
                logger.info(f"RSS取得成功: {feed_url} ({len(feed.entries)}件)")
            except Exception as e:
                logger.warning(f"RSS取得失敗 {feed_url}: {e}")
        return headlines[:self.max_keywords]

    def filter_by_genre(self, keywords: List[str]) -> List[str]:
        """ジャンルに関連するキーワードを優先（簡易フィルタ）"""
        genre_keywords = {
            "雑学・豆知識": ["なぜ", "理由", "知ってた", "実は", "秘密", "驚き"],
            "ビジネス": ["経済", "企業", "株", "市場", "仕事", "キャリア"],
            "テクノロジー": ["AI", "技術", "アプリ", "デジタル", "IT"],
            "エンタメ": ["映画", "ドラマ", "音楽", "芸能", "アニメ"],
        }
        # ジャンルフィルターがあれば優先順位を上げる（なければそのまま返す）
        return keywords

    def run(self) -> Dict[str, Any]:
        """
        トレンドキーワードを収集して返します。

        Returns:
            dict: {
                "keywords": ["キーワード1", ...],
                "headlines": ["ヘッドライン1", ...],
                "genre": "雑学・豆知識",
                "timestamp": "2026-04-14T09:00:00"
            }
        """
        logger.info("=== Agent 1: トレンド取得開始 ===")

        google_keywords = self.get_google_trends()
        rss_headlines = self.get_rss_headlines()

        # キーワードとヘッドラインをマージ
        all_keywords = list(dict.fromkeys(google_keywords + rss_headlines))
        filtered = self.filter_by_genre(all_keywords)

        result = {
            "keywords": filtered[:self.max_keywords],
            "headlines": rss_headlines[:3],
            "genre": self.genre,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Agent 1 完了: {result['keywords']}")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    agent = TrendAgent()
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
