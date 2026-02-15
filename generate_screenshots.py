"""Generate MS Store submission screenshots for ClaudeMonitor."""

import os
from PIL import Image, ImageDraw, ImageFont

# Output dimensions (Full HD)
WIDTH, HEIGHT = 1920, 1080

# Colors
BG_DARK = "#0d1117"
BG_CARD = "#1e1e2e"
ACCENT_ORANGE = "#e8a04a"
ACCENT_YELLOW = "#f5c542"
ACCENT_DEEP = "#d4783a"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
CARD_BORDER = "#313244"


def load_font(size, bold=False):
    """Load Korean-compatible font (Malgun Gothic first)."""
    font_names = [
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def create_screenshot_1():
    """Screenshot 1: Main widget showcase with dark desktop background."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle gradient-like effect with circles
    for i in range(3):
        cx = WIDTH // 2 + (i - 1) * 400
        cy = HEIGHT // 2
        r = 500
        for step in range(50):
            alpha_r = r - step * 10
            if alpha_r <= 0:
                break
            c = min(25 + step, 40)
            draw.ellipse(
                [cx - alpha_r, cy - alpha_r, cx + alpha_r, cy + alpha_r],
                fill=(c, c + 5, c + 15),
            )

    # Re-draw base to clean up
    img_base = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw_base = ImageDraw.Draw(img_base)

    # Subtle radial gradient in center
    for r in range(600, 0, -2):
        intensity = int(13 + (600 - r) * 0.02)
        color = (intensity, intensity + 2, intensity + 8)
        draw_base.ellipse(
            [WIDTH // 2 - r, HEIGHT // 2 - r, WIDTH // 2 + r, HEIGHT // 2 + r],
            fill=color,
        )

    img = img_base
    draw = ImageDraw.Draw(img)

    # Title text
    font_title = load_font(52, bold=True)
    font_subtitle = load_font(28)

    title = "Claude AI 사용량 모니터"
    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox_t[2] - bbox_t[0]
    draw.text(((WIDTH - tw) // 2, 80), title, fill=TEXT_PRIMARY, font=font_title)

    subtitle = "실시간으로 Claude API 사용량을 데스크톱 위젯에서 확인하세요"
    bbox_s = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((WIDTH - sw) // 2, 150), subtitle, fill=TEXT_SECONDARY, font=font_subtitle)

    # Load and place the widget screenshot in center
    script_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot_path = os.path.join(script_dir, "assets", "screenshot.png")

    if os.path.exists(screenshot_path):
        widget_img = Image.open(screenshot_path).convert("RGBA")

        # Scale up the widget (2x)
        scale = 2.2
        new_w = int(widget_img.width * scale)
        new_h = int(widget_img.height * scale)
        widget_img = widget_img.resize((new_w, new_h), Image.LANCZOS)

        # Center position
        wx = (WIDTH - new_w) // 2
        wy = 220

        # Drop shadow
        shadow_offset = 15
        shadow_blur = 30
        draw.rounded_rectangle(
            [wx + shadow_offset, wy + shadow_offset,
             wx + new_w + shadow_offset, wy + new_h + shadow_offset],
            radius=20,
            fill=(0, 0, 0),
        )

        # Paste widget
        img.paste(widget_img, (wx, wy), widget_img)

    # Bottom feature badges
    font_badge = load_font(22, bold=True)
    font_badge_desc = load_font(16)
    badges = [
        ("실시간 모니터링", "5시간/일별/모델별 사용량"),
        ("자동 갱신", "주기적 API 사용량 업데이트"),
        ("시스템 트레이", "항상 접근 가능한 트레이 아이콘"),
    ]

    badge_w = 340
    badge_h = 90
    total_badges_w = len(badges) * badge_w + (len(badges) - 1) * 30
    start_x = (WIDTH - total_badges_w) // 2
    badge_y = HEIGHT - 150

    for i, (title_text, desc) in enumerate(badges):
        x = start_x + i * (badge_w + 30)

        # Badge background
        draw_rounded_rect(
            draw,
            [x, badge_y, x + badge_w, badge_y + badge_h],
            radius=12,
            fill=BG_CARD,
            outline=CARD_BORDER,
            width=1,
        )

        # Orange dot indicator
        dot_cx = x + 22
        dot_cy = badge_y + 28
        draw.ellipse([dot_cx - 6, dot_cy - 6, dot_cx + 6, dot_cy + 6], fill=ACCENT_ORANGE)

        # Title
        draw.text((x + 40, badge_y + 15), title_text, fill=TEXT_PRIMARY, font=font_badge)

        # Description
        draw.text((x + 40, badge_y + 50), desc, fill=TEXT_SECONDARY, font=font_badge_desc)

    return img


def create_screenshot_2():
    """Screenshot 2: Feature highlights with cards layout."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle gradient
    for r in range(700, 0, -2):
        intensity = int(13 + (700 - r) * 0.015)
        color = (intensity, intensity + 1, intensity + 6)
        draw.ellipse(
            [WIDTH // 2 - r, HEIGHT // 2 - r, WIDTH // 2 + r, HEIGHT // 2 + r],
            fill=color,
        )

    # App icon at top
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "msix", "Assets", "Square310x310Logo.png")
    if os.path.exists(icon_path):
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((80, 80), Image.LANCZOS)
        icon_x = (WIDTH - 80) // 2
        img.paste(icon, (icon_x, 50), icon)

    # Title
    font_title = load_font(48, bold=True)
    font_subtitle = load_font(26)

    title = "ClaudeMonitor"
    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox_t[2] - bbox_t[0]
    draw.text(((WIDTH - tw) // 2, 145), title, fill=TEXT_PRIMARY, font=font_title)

    subtitle = "Claude Code API 사용량 데스크톱 위젯"
    bbox_s = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((WIDTH - sw) // 2, 210), subtitle, fill=TEXT_SECONDARY, font=font_subtitle)

    # Feature cards (2 rows x 3 cols)
    font_card_title = load_font(26, bold=True)
    font_card_desc = load_font(18)

    features = [
        ("사용량 대시보드",
         "5시간, 일별(7일), 모델별 사용량을\n프로그레스 바로 직관적 확인"),
        ("실시간 카운트다운",
         "리셋까지 남은 시간을\n실시간으로 표시"),
        ("OAuth 인증",
         "Claude OAuth를 통한\n안전한 API 접근"),
        ("시스템 트레이",
         "최소화해도 트레이에서\n빠른 접근 가능"),
        ("다크 테마",
         "눈에 편한 다크 모드\n데스크톱 위젯"),
        ("커스텀 설정",
         "갱신 주기, 투명도,\n위치 등 자유 설정"),
    ]

    card_w = 360
    card_h = 170
    gap_x = 40
    gap_y = 30
    cols = 3
    rows = 2
    total_w = cols * card_w + (cols - 1) * gap_x
    total_h = rows * card_h + (rows - 1) * gap_y
    start_x = (WIDTH - total_w) // 2
    start_y = 290

    accent_colors = [ACCENT_YELLOW, ACCENT_ORANGE, ACCENT_DEEP,
                     ACCENT_DEEP, ACCENT_ORANGE, ACCENT_YELLOW]

    for i, (ftitle, fdesc) in enumerate(features):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        # Card background
        draw_rounded_rect(
            draw,
            [x, y, x + card_w, y + card_h],
            radius=16,
            fill=BG_CARD,
            outline=CARD_BORDER,
            width=1,
        )

        # Accent bar at top
        accent_color = accent_colors[i]
        draw.rounded_rectangle(
            [x, y, x + card_w, y + 4],
            radius=2,
            fill=accent_color,
        )

        # Orange dot + Title
        dot_cx = x + 30
        dot_cy = y + 35
        draw.ellipse([dot_cx - 8, dot_cy - 8, dot_cx + 8, dot_cy + 8], fill=accent_color)
        draw.text((x + 50, y + 20), ftitle, fill=TEXT_PRIMARY, font=font_card_title)

        # Description (multi-line)
        desc_y = y + 65
        for line in fdesc.split("\n"):
            draw.text((x + 20, desc_y), line, fill=TEXT_SECONDARY, font=font_card_desc)
            desc_y += 28

    # Bottom tagline
    font_bottom = load_font(20)
    tagline = "Windows 10/11 데스크톱 위젯  •  시스템 트레이 지원  •  가볍고 빠른 실행"
    bbox_b = draw.textbbox((0, 0), tagline, font=font_bottom)
    bw = bbox_b[2] - bbox_b[0]
    draw.text(((WIDTH - bw) // 2, HEIGHT - 80), tagline, fill=TEXT_SECONDARY, font=font_bottom)

    return img


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "store_assets")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating MS Store screenshots...")

    # Screenshot 1
    ss1 = create_screenshot_1()
    ss1_path = os.path.join(output_dir, "screenshot_1.png")
    ss1.save(ss1_path, "PNG")
    print(f"  Created screenshot_1.png (1920x1080)")

    # Screenshot 2
    ss2 = create_screenshot_2()
    ss2_path = os.path.join(output_dir, "screenshot_2.png")
    ss2.save(ss2_path, "PNG")
    print(f"  Created screenshot_2.png (1920x1080)")

    print(f"\nAll screenshots saved to: {output_dir}")


if __name__ == "__main__":
    main()
