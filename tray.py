import threading
import pystray
from PIL import Image, ImageDraw


def _create_default_icon() -> Image.Image:
    """Create a ClaudeMonitor-style icon with gauge/meter design."""
    import math

    # Render at 4x for anti-aliasing
    scale = 4
    size = 64 * scale  # 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded rectangle background (#1e1e2e)
    pad = int(size * 0.06)
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill="#1e1e2e",
    )
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        outline="#313244",
        width=max(1, int(size * 0.01)),
    )

    cx, cy = size // 2, size // 2

    # Circular gauge arc (background track)
    gauge_r = int(size * 0.28)
    track_width = max(2, int(size * 0.06))
    bbox = [cx - gauge_r, cy - gauge_r, cx + gauge_r, cy + gauge_r]
    draw.arc(bbox, start=135, end=405, fill="#45475a", width=track_width)

    # Filled portion (~70% in orange accent)
    fill_end = 135 + int(270 * 0.70)
    draw.arc(bbox, start=135, end=fill_end, fill="#e8a04a", width=track_width)

    # Dot at end of filled arc
    end_angle = math.radians(fill_end)
    dot_x = cx + gauge_r * math.cos(end_angle)
    dot_y = cy + gauge_r * math.sin(end_angle)
    dot_r = max(1, int(size * 0.025))
    draw.ellipse(
        [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
        fill="#e8a04a",
    )

    # Center: small bar chart (3 bars)
    bar_w = max(1, int(size * 0.045))
    bar_gap = max(1, int(size * 0.03))
    bar_heights = [0.12, 0.18, 0.14]
    total_w = len(bar_heights) * bar_w + (len(bar_heights) - 1) * bar_gap
    bar_start_x = cx - total_w // 2
    bar_base_y = cy + int(size * 0.08)

    colors = ["#f5c542", "#e8a04a", "#d4783a"]
    for i, (h_ratio, color) in enumerate(zip(bar_heights, colors)):
        x = bar_start_x + i * (bar_w + bar_gap)
        bar_h = int(size * h_ratio)
        draw.rounded_rectangle(
            [x, bar_base_y - bar_h, x + bar_w, bar_base_y],
            radius=max(1, bar_w // 3),
            fill=color,
        )

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
            pystray.MenuItem("☕ 후원하기", self._open_donate),
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

    def _open_donate(self):
        self.widget.after(0, self.widget._open_donate)

    def _exit(self):
        self.stop()
        self.widget.after(0, self.widget.destroy)
