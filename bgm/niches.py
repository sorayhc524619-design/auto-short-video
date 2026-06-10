"""
niches.py - BGMニッチ（ジャンル）プリセット定義
2026年6月時点の調査に基づく、米国市場でRPMが高く競合が少ないニッチを収録。

各ニッチには以下が含まれます:
  - suno_prompts: Suno AIのStyle欄にそのまま貼るプロンプト（英語）
  - visual_prompt: 背景画像生成用プロンプト（Stability AI用）
  - fallback_colors: 画像APIなしの場合のグラデーション色
  - title_templates: YouTubeタイトルのテンプレート（英語）
  - description_intro: 説明文の冒頭（英語）
  - tags: YouTube検索タグ
"""

NICHES = {
    # 睡眠×雨音系: RPM $10-25、競合が少なく成長率が高い最有力ニッチ
    "rain_sleep": {
        "display_name": "Rain & Piano Sleep Ambient",
        "suno_prompts": [
            "ambient sleep music, soft felt piano, gentle rain on window, warm analog pads, 55 bpm, no drums, deeply calming, instrumental",
            "peaceful sleep ambient, slow piano melody, distant thunder, soft rain texture, lush reverb, dreamy, instrumental, no vocals",
            "calm nocturne piano, light rainfall ambience, subtle string swells, very slow tempo, soothing bedtime music, instrumental",
            "minimal ambient piano, rainy night atmosphere, warm sub bass drone, airy pads, meditative, sleep inducing, instrumental",
            "gentle lullaby piano, soft rain and wind, music box accents, ethereal pads, extremely relaxing, instrumental, no vocals",
        ],
        "visual_prompt": (
            "cozy bedroom window at night with rain drops on glass, warm lamp glow, "
            "soft bokeh city lights in the distance, cinematic, photorealistic, "
            "moody and calming atmosphere, 16:9"
        ),
        "fallback_colors": ((18, 24, 48), (52, 64, 110)),
        "title_templates": [
            "Rain Sounds & Soft Piano for Deep Sleep 🌧️ Fall Asleep Fast, Relaxing Ambient Music ({hours})",
            "Gentle Rain + Calm Piano 🌧️ Deep Sleep Music, Insomnia Relief, Stress Relief ({hours})",
        ],
        "description_intro": (
            "Gentle rain and soft piano to help you fall asleep fast, relieve stress, "
            "and calm your mind. Perfect for deep sleep, insomnia relief, studying, or relaxing."
        ),
        "tags": [
            "sleep music", "rain sounds", "deep sleep", "relaxing music", "piano sleep music",
            "insomnia relief", "calm music", "ambient sleep", "rain piano", "fall asleep fast",
            "stress relief music", "bedtime music",
        ],
    },

    # ダークアカデミア/ファンタジー系: 読書・TRPG勢に保存率が高い低競合ニッチ
    "dark_academia": {
        "display_name": "Dark Academia / Fantasy Library Ambience",
        "suno_prompts": [
            "dark academia ambience, melancholic solo cello, old library atmosphere, soft vinyl crackle, fireplace warmth, slow classical, instrumental",
            "fantasy library music, gentle harp and strings, candlelight mood, medieval undertones, mysterious and cozy, instrumental, no vocals",
            "moody chamber music, piano and viola duet, rainy university library, scholarly atmosphere, wistful, slow tempo, instrumental",
            "enchanted study ambience, music box and soft strings, magical academia, warm and nostalgic, quiet intensity, instrumental",
            "gothic study music, subdued organ pads, distant choir hum, ancient library mood, contemplative, instrumental, no vocals",
        ],
        "visual_prompt": (
            "ancient candlelit library with towering bookshelves, fireplace glow, "
            "leather armchair, rain outside gothic windows, dark academia aesthetic, "
            "cinematic, painterly, warm shadows, 16:9"
        ),
        "fallback_colors": ((38, 26, 18), (96, 64, 38)),
        "title_templates": [
            "Dark Academia Library Ambience 📚 Cozy Study Music with Fireplace & Rain ({hours})",
            "You're Studying in an Ancient Library 🕯️ Dark Academia Music for Reading & Focus ({hours})",
        ],
        "description_intro": (
            "Step into an ancient candlelit library. Cozy dark academia music with fireplace "
            "crackle and rain, perfect for studying, reading, writing, or tabletop RPG sessions."
        ),
        "tags": [
            "dark academia", "study music", "library ambience", "reading music", "fantasy music",
            "cozy ambience", "focus music", "writing music", "classical study music", "dnd music",
            "studying playlist", "fireplace sounds",
        ],
    },

    # 定番lofi: 競合は多いが需要が最大。独自ビジュアルで差別化前提
    "lofi_study": {
        "display_name": "Lofi Hip Hop Study & Chill",
        "suno_prompts": [
            "chill lofi hip hop, dusty drums, warm Rhodes piano, vinyl crackle, mellow jazzy chords, 75 bpm, relaxed study beat, instrumental",
            "lofi chillhop, soft electric piano, tape saturation, laid back boom bap drums, night city mood, instrumental, no vocals",
            "cozy lofi beat, muted trumpet melody, jazzy guitar licks, rain ambience layer, nostalgic and warm, instrumental",
            "dreamy lofi hip hop, bell keys, slow swung drums, deep mellow bass, late night studying vibe, instrumental",
            "calm lofi groove, soft saxophone, brushed drums, analog warmth, coffee shop atmosphere, instrumental, no vocals",
        ],
        "visual_prompt": (
            "cozy desk by a window at dusk, warm desk lamp, notebooks and coffee mug, "
            "city skyline with soft purple sunset, lofi anime illustration style, "
            "detailed, atmospheric, 16:9"
        ),
        "fallback_colors": ((44, 28, 56), (120, 80, 130)),
        "title_templates": [
            "Lofi Hip Hop Radio 📻 Chill Beats to Study, Work & Relax ({hours})",
            "Late Night Lofi 🌙 Chill Beats for Deep Focus & Study Sessions ({hours})",
        ],
        "description_intro": (
            "Chill lofi hip hop beats to help you study, work, code, or just relax. "
            "Smooth jazzy chords, dusty drums, and warm analog vibes."
        ),
        "tags": [
            "lofi", "lofi hip hop", "study music", "chill beats", "lofi beats", "work music",
            "focus music", "chillhop", "relaxing beats", "study with me", "coding music",
            "concentration music",
        ],
    },

    # 宇宙アンビエント: 睡眠×SFで保存率・連続再生時間が長い
    "space_ambient": {
        "display_name": "Deep Space Sleep Ambient",
        "suno_prompts": [
            "deep space ambient, vast slow pads, cosmic drone, shimmering textures, weightless and serene, no drums, no melody, instrumental",
            "interstellar sleep music, evolving synth pads, sub bass drone, distant celestial tones, extremely slow and calm, instrumental",
            "cosmic meditation ambient, warm analog drones, gentle frequency sweeps, floating in space feeling, peaceful, instrumental, no vocals",
            "ethereal space soundscape, soft choir pads, deep drone foundation, twinkling high textures, sleep inducing, instrumental",
            "dark ambient space music, low rumbling drone, sparse glassy tones, infinite void atmosphere, hypnotic and calm, instrumental",
        ],
        "visual_prompt": (
            "breathtaking view of a nebula and distant stars from a spaceship window, "
            "deep blues and purples, soft cosmic glow, ultra detailed digital art, "
            "serene and vast, 16:9"
        ),
        "fallback_colors": ((8, 10, 28), (40, 30, 80)),
        "title_templates": [
            "Deep Space Ambient for Sleep 🌌 Cosmic Relaxation, Drift Into Deep Sleep ({hours})",
            "Floating Through the Cosmos 🌌 Space Ambient Music for Sleep & Meditation ({hours})",
        ],
        "description_intro": (
            "Drift through the cosmos with deep space ambient music. Vast, slowly evolving "
            "soundscapes for deep sleep, meditation, focus, and total relaxation."
        ),
        "tags": [
            "space ambient", "sleep music", "ambient music", "deep sleep", "meditation music",
            "cosmic music", "relaxation", "drone ambient", "sleep sounds", "interstellar",
            "calm music", "space sounds",
        ],
    },
}

DEFAULT_NICHE = "rain_sleep"
