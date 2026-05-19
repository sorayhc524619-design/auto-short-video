"""
混合肌・インナードライ肌に乳液は必要？ベタつかない選び方と使い方を解説
記事アイキャッチ画像を生成するスクリプト。

水分と油分のバランスをテーマに、爽やかなブルー〜クリア系の配色で
"うるおい"と"軽さ"を両立した世界観に仕上げる。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONT_GOTHIC_P = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"

WIDTH, HEIGHT = 1200, 630

# 混合肌・インナードライをイメージした、みずみずしいブルー系
TOP_COLOR = (239, 248, 251)        # 上：ほぼ白〜淡い水色
BOTTOM_COLOR = (206, 226, 234)     # 下：くすみアクアブルー
ACCENT_COLOR = (58, 116, 140)      # アクセント：深いティールブルー
MAIN_TEXT_COLOR = (32, 56, 72)     # メイン文字：ネイビーに近いダークブルー
SUB_TEXT_COLOR = (90, 118, 134)    # サブ文字：グレイッシュブルー


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
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 左上に大きめのハイライト円
    draw.ellipse((-180, -200, 420, 400), fill=(255, 255, 255, 130))
    # 右下に淡いアクアの円
    draw.ellipse((780, 380, 1340, 820), fill=(170, 210, 224, 110))
    # 右上に小さめの透明感のある円
    draw.ellipse((900, 40, 1140, 280), fill=(220, 240, 248, 120))
    # 左下に水滴感のあるアクセント
    draw.ellipse((-60, 420, 240, 720), fill=(190, 220, 232, 95))

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

    main_font = ImageFont.truetype(FONT_GOTHIC, 56)
    question_font = ImageFont.truetype(FONT_GOTHIC, 70)
    sub_font = ImageFont.truetype(FONT_GOTHIC_P, 34)
    label_font = ImageFont.truetype(FONT_GOTHIC_P, 22)
    small_font = ImageFont.truetype(FONT_GOTHIC_P, 20)

    # 上部ラベル
    label_text = "SKIN CARE  |  混合肌・インナードライ"
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = bbox[2] - bbox[0]
    label_h = bbox[3] - bbox[1]
    label_x = (WIDTH - label_w) // 2
    label_y = 78
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

    # メインタイトル（質問形式を大きく見せる）
    title_line1 = "乳液は本当に必要？"
    title_line2 = "混合肌・インナードライの"
    title_line3 = "ベタつかない選び方と使い方"

    # 質問を一番強く
    draw_centered_text(
        draw, title_line1, question_font, y=180, width=WIDTH,
        fill=MAIN_TEXT_COLOR, letter_spacing=4,
    )

    # 区切り線
    line_y = 280
    line_len = 70
    draw.line(
        (WIDTH // 2 - line_len, line_y, WIDTH // 2 + line_len, line_y),
        fill=ACCENT_COLOR, width=2,
    )

    draw_centered_text(
        draw, title_line2, sub_font, y=305, width=WIDTH,
        fill=SUB_TEXT_COLOR, letter_spacing=3,
    )
    draw_centered_text(
        draw, title_line3, main_font, y=360, width=WIDTH,
        fill=MAIN_TEXT_COLOR, letter_spacing=3,
    )

    # 下部キャッチコピー
    catch = "うるおい、ちゃんと閉じ込めよう。"
    draw_centered_text(
        draw, catch, small_font, y=480, width=WIDTH,
        fill=ACCENT_COLOR, letter_spacing=8,
    )

    # 左右のドット
    for x in [WIDTH // 2 - 220, WIDTH // 2 + 220]:
        draw.ellipse((x - 4, 482, x + 4, 490), fill=ACCENT_COLOR)

    # フッター
    footer = "2026.05.19   skincare column"
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    fw = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - fw) // 2, HEIGHT - 60),
        footer, font=small_font, fill=SUB_TEXT_COLOR,
    )

    out_path = OUTPUT_DIR / "skincare_milky_lotion.png"
    background.save(out_path, "PNG", optimize=True)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
