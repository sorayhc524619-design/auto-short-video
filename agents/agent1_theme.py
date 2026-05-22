"""
agent1_theme.py - Agent 1: テーマ生成
Claude APIで「Cinematic Sleep Music」用のテーマ・英語タイトル・Sunoプロンプト・
ビジュアルプロンプトをJSONで生成します。
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


THEME_PROMPT = """You are a YouTube content strategist for a faceless "Cinematic Sleep Music" channel targeting English-speaking (US) viewers.
Generate ONE original video concept that will rank well on YouTube and avoid the "Inauthentic Content" demonetization policy by having a strong, specific theme.

Channel niche: {niche}
Target video length: {duration_min} minutes
Number of distinct music tracks to compose: {tracks}

Requirements:
- Pick a vivid, cinematic *scene* (e.g. "Rainy night in a Tokyo apartment", "Snowy cabin by a fireplace", "Forest stream at dawn").
- The scene must feel cozy/relaxing and pair with sleep music.
- Title must use proven SEO patterns for sleep music ("8 Hours", "Deep Sleep", "Relaxing", scene description).
- Description (under 1500 chars) should set the mood, list timestamps later (we add them), and include 5-10 relevant keywords naturally.
- Tags: 15-20 keywords mixing broad ("sleep music", "relaxing music") and specific ("rainy night", "jazz cafe").
- Music prompts: {tracks} short prompts (each ~40 words) for Suno AI. Each should describe a slightly different mood progression but stay within the same theme. Specify instruments, tempo (around 50-70 BPM), key signature, and "instrumental, no vocals, calm, smooth".
- Visual prompt: a SINGLE detailed prompt for Stable Diffusion to produce a 16:9 cinematic still image of the scene (mention lighting, camera angle, atmosphere, color palette). No text in image.
- Ambient sound: pick ONE of: rain, fireplace, forest, wind, ocean, thunder, stream, none. Must match the scene.

Output ONLY valid JSON, no markdown fences, no commentary:
{{
  "theme_name": "short internal name e.g. rainy_tokyo_apartment",
  "scene_description": "1-2 sentence vivid description",
  "english_title": "YouTube title, 60-95 chars",
  "description": "YouTube description, multiple paragraphs OK",
  "tags": ["tag1", "tag2", ...],
  "thumbnail_text": "very short overlay text e.g. 'Rainy Tokyo Night'",
  "music_prompts": [
    "prompt 1 for Suno",
    "prompt 2 for Suno",
    "..."
  ],
  "visual_prompt": "Stable Diffusion prompt",
  "ambient_sound": "rain"
}}
"""


MOCK_THEME = {
    "theme_name": "rainy_tokyo_apartment",
    "scene_description": "A small Tokyo apartment on a rainy autumn night, "
                         "warm lamplight, vinyl crackle, distant city hum.",
    "english_title": "Rainy Tokyo Apartment - Relaxing Sleep Music (Mock Test)",
    "description": "Mock pipeline test. Replace with real Claude output by removing --mock.",
    "tags": ["sleep music", "rain sounds", "tokyo", "relaxing", "lofi", "ambient", "8 hours"],
    "thumbnail_text": "Rainy Tokyo Night",
    "music_prompts": [
        "Lo-fi jazz piano with soft saxophone, 60 BPM, rainy night cafe, instrumental",
        "Warm electric piano, slow tempo, vinyl crackle, late night, instrumental",
        "Soft pad synth with rhodes, ambient texture, 55 BPM, dreamy, instrumental",
        "Acoustic guitar fingerpicking, gentle, hopeful, 65 BPM, instrumental",
        "Muted trumpet over rhodes, slow swing, intimate, 60 BPM, instrumental",
    ],
    "visual_prompt": "Cozy Japanese apartment at night, rain on window, warm yellow lamp light, "
                     "tatami floor, small desk with cup of tea, soft bokeh, cinematic, 16:9",
    "ambient_sound": "rain",
}


class ThemeAgent:
    def __init__(self):
        if config.MOCK_MODE:
            self.client = None
            return
        if not config.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY が設定されていません")
        self.client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

    def generate(self) -> Dict[str, Any]:
        if config.MOCK_MODE:
            logger.info("[MOCK] hardcoded theme を使用")
            return dict(MOCK_THEME)

        prompt = THEME_PROMPT.format(
            niche=config.CHANNEL_NICHE,
            duration_min=config.VIDEO_DURATION_SEC // 60,
            tracks=config.MUSIC_TRACKS_PER_VIDEO,
        )
        logger.info("Claudeにテーマ生成を依頼中...")
        msg = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        data = json.loads(text)
        logger.info(f"テーマ生成成功: {data.get('theme_name')} / {data.get('english_title')}")
        return data

    def run(self) -> Dict[str, Any]:
        logger.info("=== Agent 1: テーマ生成開始 ===")
        theme = self.generate()
        theme["timestamp"] = datetime.now().isoformat()
        theme["date"] = datetime.now().strftime("%Y%m%d")
        return theme


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    agent = ThemeAgent()
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
