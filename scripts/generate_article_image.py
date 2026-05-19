"""
肌荒れした日の過ごし方｜焦らず肌と心を整える余白美容
記事アイキャッチ画像を生成するスクリプト。

Pillowで日本語フォントを使い、柔らかい余白のあるデザインに仕上げる。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONT_GOTHIC_P = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"

WIDTH, HEIGHT = 1200, 630  # ブログのOG画像サイズ

# 肌に寄り添う余白美容らしい、淡いベージュ〜ピンクのグラデーション
TOP_COLOR = (250, 240, 233)      # 上：温かみのあるアイボリー
BOTTOM_COLOR = (243, 220, 215)   # 下：くすみピンクベージュ
ACCENT_COLOR = (181, 130, 116)   # アクセント：テラコッタブラウン
MAIN_TEXT_COLOR = (61, 47, 41)   # メイン文字：濃いブラウン
SUB_TEXT_COLOR = (130, 105, 96)  # サブ文字：ミディアムブラウン


def make_gradient_background(width: int, height: int) -> Image.Image:
    base = Image.new("RGB", (width, height), TOP_COLOR)
    pixels = base.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(TOP_COLOR[0] * (1 - t) + BOTTOM_COLOR[0] * t)
        g = int(TOP_COLOR[1] * (1 - t) + BOTTOM_COLOR[1] * t)
        b = int(TOP_COLOR[2] * (1 - t) + BOTTOM_COLOR[2] * t)
        for x in range(width):
            pixels[x, y] = (r, g, b)
    return base


def add_soft_circles(img: Image.Image) -> Image.Image:
    """背景に柔らかい円形のグロウを足して、ゆったりした空気感を演出。"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 左上に大きめの淡い円
    draw.ellipse(
        (-220, -180, 380, 420),
        fill=(255, 248, 238, 110),
    )
    # 右下にやさしいピンクの円
    draw.ellipse(
        (820, 360, 1340, 820),
        fill=(238, 200, 196, 95),
    )
    # 中央右に薄いハイライト
    draw.ellipse(
        (780, 80, 1080, 320),
        fill=(255, 252, 246, 80),
    )

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=60))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    y: int,
    width: int,
    fill,
    letter_spacing: int = 0,
):
    if letter_spacing == 0:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2 - bbox[0]
        draw.text((x, y), text, font=font, fill=fill)
        return

    # 文字間隔を広げて描画
    widths = []
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        widths.append(bbox[2] - bbox[0])
    total_w = sum(widths) + letter_spacing * (len(text) - 1)
    x = (width - total_w) // 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + letter_spacing


def main():
    background = make_gradient_background(WIDTH, HEIGHT)
    background = add_soft_circles(background).convert("RGB")

    draw = ImageDraw.Draw(background)

    # フォント
    main_font = ImageFont.truetype(FONT_GOTHIC, 64)
    sub_font = ImageFont.truetype(FONT_GOTHIC_P, 38)
    label_font = ImageFont.truetype(FONT_GOTHIC_P, 22)
    small_font = ImageFont.truetype(FONT_GOTHIC_P, 20)

    # 上部：カテゴリーラベル（細い枠付き）
    label_text = "SKIN CARE  |  余白美容"
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = bbox[2] - bbox[0]
    label_h = bbox[3] - bbox[1]
    label_x = (WIDTH - label_w) // 2
    label_y = 90
    padding_x, padding_y = 28, 14
    draw.rounded_rectangle(
        (
            label_x - padding_x,
            label_y - padding_y,
            label_x + label_w + padding_x,
            label_y + label_h + padding_y + 6,
        ),
        radius=999,
        outline=ACCENT_COLOR,
        width=2,
    )
    draw.text((label_x, label_y), label_text, font=label_font, fill=ACCENT_COLOR)

    # メインタイトル（2行に分割）
    title_line1 = "肌荒れした日の過ごし方"
    title_line2 = "焦らず肌と心を整える、余白美容。"

    draw_centered_text(
        draw, title_line1, main_font, y=220, width=WIDTH,
        fill=MAIN_TEXT_COLOR, letter_spacing=6,
    )

    # 区切りの細い線
    line_y = 320
    line_len = 80
    draw.line(
        (WIDTH // 2 - line_len, line_y, WIDTH // 2 + line_len, line_y),
        fill=ACCENT_COLOR, width=2,
    )

    draw_centered_text(
        draw, title_line2, sub_font, y=355, width=WIDTH,
        fill=SUB_TEXT_COLOR, letter_spacing=3,
    )

    # 下部：補足のキャッチコピー
    catch = "ゆらぎ肌に効く、休む勇気。"
    draw_centered_text(
        draw, catch, small_font, y=460, width=WIDTH,
        fill=ACCENT_COLOR, letter_spacing=8,
    )

    # 装飾：左右の小さなドット
    for i, x in enumerate([WIDTH // 2 - 200, WIDTH // 2 + 200]):
        draw.ellipse((x - 4, 462, x + 4, 470), fill=ACCENT_COLOR)

    # フッター日付
    footer = "2026.05.19   skincare column"
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    fw = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - fw) // 2, HEIGHT - 60),
        footer, font=small_font, fill=SUB_TEXT_COLOR,
    )

    out_path = OUTPUT_DIR / "skincare_yohaku_beauty.png"
    background.save(out_path, "PNG", optimize=True)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
