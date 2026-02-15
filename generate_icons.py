"""Generate ClaudeMonitor icon assets for MSIX packaging and system tray."""

import math
import os
from PIL import Image, ImageDraw


def create_icon(size: int) -> Image.Image:
    """Create the ClaudeMonitor icon at the given size.

    Design: Dark rounded rectangle with a minimal usage gauge/meter symbol.
    Colors match the app's Catppuccin-inspired dark theme.
    """
    # Render at 4x for anti-aliasing
    scale = 4
    canvas = size * scale
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: dark rounded rectangle (#1e1e2e)
    pad = int(canvas * 0.06)
    radius = int(canvas * 0.22)
    draw.rounded_rectangle(
        [pad, pad, canvas - pad, canvas - pad],
        radius=radius,
        fill="#1e1e2e",
    )

    # Subtle border glow
    draw.rounded_rectangle(
        [pad, pad, canvas - pad, canvas - pad],
        radius=radius,
        outline="#313244",
        width=max(1, int(canvas * 0.01)),
    )

    cx, cy = canvas // 2, canvas // 2

    # Draw circular gauge arc (background track)
    gauge_r = int(canvas * 0.28)
    track_width = max(2, int(canvas * 0.06))
    bbox = [cx - gauge_r, cy - gauge_r, cx + gauge_r, cy + gauge_r]

    # Background track (dark gray)
    draw.arc(bbox, start=135, end=405, fill="#45475a", width=track_width)

    # Filled portion of gauge (~70% fill in orange accent)
    fill_end = 135 + int(270 * 0.70)
    draw.arc(bbox, start=135, end=fill_end, fill="#e8a04a", width=track_width)

    # Small dot at the end of the filled arc
    end_angle = math.radians(fill_end)
    dot_x = cx + gauge_r * math.cos(end_angle)
    dot_y = cy + gauge_r * math.sin(end_angle)
    dot_r = max(1, int(canvas * 0.025))
    draw.ellipse(
        [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
        fill="#e8a04a",
    )

    # Center text-like element: small bar chart (3 bars)
    bar_w = max(1, int(canvas * 0.045))
    bar_gap = max(1, int(canvas * 0.03))
    bar_heights = [0.12, 0.18, 0.14]  # relative to canvas
    total_w = len(bar_heights) * bar_w + (len(bar_heights) - 1) * bar_gap
    bar_start_x = cx - total_w // 2
    bar_base_y = cy + int(canvas * 0.08)

    colors = ["#f5c542", "#e8a04a", "#d4783a"]  # yellow, orange, deep orange
    for i, (h_ratio, color) in enumerate(zip(bar_heights, colors)):
        x = bar_start_x + i * (bar_w + bar_gap)
        bar_h = int(canvas * h_ratio)
        draw.rounded_rectangle(
            [x, bar_base_y - bar_h, x + bar_w, bar_base_y],
            radius=max(1, bar_w // 3),
            fill=color,
        )

    # Downscale with anti-aliasing
    img = img.resize((size, size), Image.LANCZOS)
    return img


def create_wide_tile(width: int, height: int) -> Image.Image:
    """Create a wide tile with the icon centered and app name."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background
    radius = int(min(width, height) * 0.05)
    draw.rounded_rectangle(
        [0, 0, width, height],
        radius=radius,
        fill="#1e1e2e",
    )

    # Place icon in center
    icon_size = int(height * 0.6)
    icon = create_icon(icon_size)
    x = (width - icon_size) // 2
    y = (height - icon_size) // 2
    img.paste(icon, (x, y), icon)

    return img


def generate_all():
    """Generate all required icon assets for MSIX packaging."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msix", "Assets")
    os.makedirs(output_dir, exist_ok=True)

    # Square icons
    square_assets = {
        "Square44x44Logo.png": 44,
        "Square44x44Logo.scale-200.png": 88,
        "Square150x150Logo.png": 150,
        "Square150x150Logo.scale-200.png": 300,
        "Square310x310Logo.png": 310,
        "StoreLogo.png": 50,
        "StoreLogo.scale-200.png": 100,
    }

    for filename, size in square_assets.items():
        icon = create_icon(size)
        path = os.path.join(output_dir, filename)
        icon.save(path, "PNG")
        print(f"  Created {filename} ({size}x{size})")

    # Wide tile
    wide = create_wide_tile(310, 150)
    wide_path = os.path.join(output_dir, "Wide310x150Logo.png")
    wide.save(wide_path, "PNG")
    print(f"  Created Wide310x150Logo.png (310x150)")

    # ICO file (multi-size)
    ico_sizes = [16, 32, 48, 256]
    ico_images = [create_icon(s) for s in ico_sizes]
    ico_path = os.path.join(output_dir, "icon.ico")
    # PIL ICO save: first image is the base, append_images adds the rest
    ico_images[-1].save(
        ico_path, format="ICO",
        append_images=ico_images[:-1],
    )
    print(f"  Created icon.ico (sizes: {ico_sizes})")

    # Also save a 64x64 PNG for tray fallback
    tray_icon = create_icon(64)
    tray_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png"
    )
    tray_icon.save(tray_path, "PNG")
    print(f"  Created assets/icon.png (64x64 tray icon)")

    print(f"\nAll assets generated in: {output_dir}")


if __name__ == "__main__":
    print("Generating ClaudeMonitor icon assets...")
    generate_all()
