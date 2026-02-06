import threading
import pystray
from PIL import Image, ImageDraw


def _create_default_icon() -> Image.Image:
    """Create a Claude-style icon with sparkle mark."""
    # Render at 4x for anti-aliasing
    scale = 4
    size = 64 * scale  # 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background with Claude-like warm gradient
    # Base: warm beige-orange (#D4A574)
    pad = 4 * scale
    radius = 14 * scale
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill="#D4A574",
    )

    # Add subtle darker inner shadow at bottom
    for i in range(8 * scale):
        alpha = int(30 * (1 - i / (8 * scale)))
        y_off = size - pad - i
        draw.line(
            [(pad + radius, y_off), (size - pad - radius, y_off)],
            fill=(140, 90, 50, alpha),
        )

    # Add lighter highlight at top
    for i in range(6 * scale):
        alpha = int(40 * (1 - i / (6 * scale)))
        y_off = pad + i
        draw.line(
            [(pad + radius, y_off), (size - pad - radius, y_off)],
            fill=(255, 230, 200, alpha),
        )

    # Draw Claude sparkle (✦) - a 4-pointed star
    cx, cy = size // 2, size // 2
    star_r = 18 * scale  # outer radius
    star_inner = 5 * scale  # inner radius

    # 4-pointed star vertices
    import math
    points = []
    for i in range(8):
        angle = math.radians(i * 45 - 90)  # start from top
        r = star_r if i % 2 == 0 else star_inner
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))

    draw.polygon(points, fill="white")

    # Downscale with anti-aliasing
    img = img.resize((64, 64), Image.LANCZOS)
    return img


class TrayManager:
    def __init__(self, widget):
        self.widget = widget
        self.icon = None

    def start(self):
        # Try to load icon from file, fallback to generated
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                image = _create_default_icon()
        except Exception:
            image = _create_default_icon()

        menu = pystray.Menu(
            pystray.MenuItem("보이기/숨기기", self._toggle_visibility, default=True),
            pystray.MenuItem("지금 새로고침", self._refresh_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("설정", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self._exit),
        )
        self.icon = pystray.Icon("ClaudeMonitor", image, "ClaudeMonitor", menu)

        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def _toggle_visibility(self):
        self.widget.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.widget.winfo_viewable():
            self.widget.withdraw()
        else:
            self.widget.deiconify()
            self.widget.attributes("-topmost", True)

    def _refresh_now(self):
        self.widget.after(0, self.widget._manual_refresh)

    def _open_settings(self):
        self.widget.after(0, self.widget._open_settings)

    def _exit(self):
        self.stop()
        self.widget.after(0, self.widget.destroy)
