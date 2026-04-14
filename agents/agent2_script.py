"""
agent2_script.py - Agent 2: スクリプト生成エージェント
Claude APIを使って60秒ショート動画用の台本を生成します。
"""

import logging
import json
from typing import Dict, Any, List

import anthropic

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


SCRIPT_PROMPT_TEMPLATE = """
あなたはショート動画のプロデューサーです。
以下の情報をもとに、視聴者を引きつける60秒のショート動画台本をJSON形式で生成してください。

## 入力情報
- 今日のトレンドキーワード: {keywords}
- コンテンツジャンル: {genre}
- 見出し情報: {headlines}

## 動画構成（合計60秒）
1. 冒頭フック（5秒）: 「えっ、本当に？」と思わせる驚きの一言
2. 本編（50秒）: 3〜4つの具体的なポイントを紹介
3. CTA（5秒）: フォロー・いいねを促す締めの一言

## 出力形式（必ずこのJSON形式で返してください）
{{
  "title": "動画タイトル（30文字以内）",
  "description": "動画説明文（100文字以内）",
  "hashtags": ["#タグ1", "#タグ2", "#タグ3", "#タグ4", "#タグ5"],
  "thumbnail_text": "サムネイル用テキスト（10文字以内）",
  "scenes": [
    {{
      "scene_id": 1,
      "duration_sec": 5,
      "type": "hook",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示（背景・テキスト・アニメーション等）",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }},
    {{
      "scene_id": 2,
      "duration_sec": 13,
      "type": "main",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }},
    {{
      "scene_id": 3,
      "duration_sec": 12,
      "type": "main",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }},
    {{
      "scene_id": 4,
      "duration_sec": 13,
      "type": "main",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }},
    {{
      "scene_id": 5,
      "duration_sec": 12,
      "type": "main",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }},
    {{
      "scene_id": 6,
      "duration_sec": 5,
      "type": "cta",
      "narration": "ナレーションテキスト",
      "visual_direction": "映像の指示",
      "on_screen_text": "画面に表示するテキスト（任意）"
    }}
  ]
}}

※ JSON以外のテキストは一切出力しないでください。
"""


class ScriptAgent:
    """Claude APIを使ってショート動画台本を生成するエージェント"""

    def __init__(self):
        if not config.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY が設定されていません")
        self.client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

    def generate_script(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        トレンドデータから台本を生成します。

        Args:
            trend_data: Agent 1の出力データ

        Returns:
            dict: 台本データ（scenes配列を含む）
        """
        keywords = ", ".join(trend_data.get("keywords", []))
        genre = trend_data.get("genre", config.CONTENT_GENRE)
        headlines = "\n".join(trend_data.get("headlines", []))

        prompt = SCRIPT_PROMPT_TEMPLATE.format(
            keywords=keywords,
            genre=genre,
            headlines=headlines if headlines else "（なし）",
        )

        logger.info(f"Claude APIに台本生成をリクエスト中... キーワード: {keywords}")

        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # JSONのパース
            # コードブロックが含まれる場合は除去
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            script_data = json.loads(response_text)
            logger.info(f"台本生成成功: {script_data.get('title', '（タイトルなし）')}")
            return script_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {e}")
            logger.debug(f"レスポンス: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Claude API エラー: {e}")
            raise

    def generate_metadata(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        動画のメタデータ（タイトル・説明・タグ）を生成/検証します。
        台本データにすでに含まれている場合はそのまま返します。
        """
        return {
            "title": script_data.get("title", "今日の雑学"),
            "description": script_data.get("description", ""),
            "hashtags": script_data.get("hashtags", ["#雑学", "#豆知識", "#shorts"]),
            "thumbnail_text": script_data.get("thumbnail_text", ""),
        }

    def run(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        トレンドデータを受け取り、完全な台本データを返します。

        Args:
            trend_data: Agent 1の出力データ

        Returns:
            dict: 台本データ + メタデータ
        """
        logger.info("=== Agent 2: スクリプト生成開始 ===")

        script = self.generate_script(trend_data)
        metadata = self.generate_metadata(script)

        # 台本にメタデータをマージ
        script.update(metadata)

        logger.info(f"Agent 2 完了: タイトル「{script.get('title')}」")
        return script


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # テスト用のダミートレンドデータ
    dummy_trend = {
        "keywords": ["ChatGPT", "AI活用", "自動化"],
        "headlines": ["AIが仕事を変える時代に突入", "生成AIの活用法まとめ"],
        "genre": "テクノロジー",
    }

    agent = ScriptAgent()
    result = agent.run(dummy_trend)
    print(json.dumps(result, ensure_ascii=False, indent=2))
