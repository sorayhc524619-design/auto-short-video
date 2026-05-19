"""
混合肌・インナードライ肌に合うクレンジングの選び方｜乾燥しにくい落とし方も解説
記事アイキャッチ画像を生成するスクリプト。

"やさしく洗い流す"を象徴する、淡いミントセージ系のグラデーションで
清潔感とうるおいを両立した世界観に仕上げる。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONT_GOTHIC_P = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"

WIDTH, HEIGHT = 1200, 630

# クレンジングのやさしい清潔感を表現する、ミントセージ〜クリーム系
TOP_COLOR = (245, 248, 240)        # 上：ほぼ白〜淡いクリーム
BOTTOM_COLOR = (210, 225, 208)     # 下：くすみセージグリーン
ACCENT_COLOR = (88, 122, 96)       # アクセント：深いセージ
MAIN_TEXT_COLOR = (40, 60, 46)     # メイン文字：濃いフォレストグリーン
SUB_TEXT_COLOR = (102, 122, 104)   # サブ文字：グレイッシュセージ


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

    # 左上に大きなハイライト
    draw.ellipse((-200, -200, 440, 420), fill=(255, 255, 250, 140))
    # 右下にやわらかいセージの円
    draw.ellipse((760, 380, 1340, 820), fill=(190, 215, 188, 110))
    # 中央右にクリーミーな光
    draw.ellipse((860, 60, 1120, 280), fill=(240, 245, 230, 120))
    # 左下に小さな泡感
    draw.ellipse((40, 470, 220, 640), fill=(220, 232, 215, 100))
    draw.ellipse((200, 530, 320, 640), fill=(220, 232, 215, 90))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=58))
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

    main_font = ImageFont.truetype(FONT_GOTHIC, 60)
    sub_main_font = ImageFont.truetype(FONT_GOTHIC, 46)
    sub_font = ImageFont.truetype(FONT_GOTHIC_P, 32)
    label_font = ImageFont.truetype(FONT_GOTHIC_P, 22)
    small_font = ImageFont.truetype(FONT_GOTHIC_P, 20)

    # 上部ラベル
    label_text = "SKIN CARE  |  CLEANSING GUIDE"
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

    # メインタイトル
    line1 = "混合肌・インナードライに合う"
    line2 = "クレンジングの選び方"
    line3 = "乾燥しにくい落とし方も解説"

    draw_centered_text(
        draw, line1, sub_main_font, y=170, width=WIDTH,
        fill=SUB_TEXT_COLOR, letter_spacing=3,
    )
    draw_centered_text(
        draw, line2, main_font, y=235, width=WIDTH,
        fill=MAIN_TEXT_COLOR, letter_spacing=6,
    )

    # 区切り線
    line_y = 335
    line_len = 75
    draw.line(
        (WIDTH // 2 - line_len, line_y, WIDTH // 2 + line_len, line_y),
        fill=ACCENT_COLOR, width=2,
    )

    draw_centered_text(
        draw, line3, sub_font, y=360, width=WIDTH,
        fill=SUB_TEXT_COLOR, letter_spacing=3,
    )

    # 下部キャッチコピー
    catch = "落としすぎない、を、味方に。"
    draw_centered_text(
        draw, catch, small_font, y=470, width=WIDTH,
        fill=ACCENT_COLOR, letter_spacing=8,
    )

    # 左右のドット
    for x in [WIDTH // 2 - 220, WIDTH // 2 + 220]:
        draw.ellipse((x - 4, 472, x + 4, 480), fill=ACCENT_COLOR)

    # フッター
    footer = "2026.05.19   skincare column"
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    fw = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - fw) // 2, HEIGHT - 60),
        footer, font=small_font, fill=SUB_TEXT_COLOR,
    )

    out_path = OUTPUT_DIR / "skincare_cleansing_guide.png"
    background.save(out_path, "PNG", optimize=True)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
