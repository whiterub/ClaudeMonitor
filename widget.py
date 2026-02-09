import threading
from datetime import datetime, timezone

import customtkinter as ctk

from api_client import UsageData, ApiResult, OAuthClient
from config import Config
from utils import get_usage_color, format_countdown


UI_PRESETS = {
    "small": {
        "width": 200, "row_height": 38, "title_height": 24, "status_height": 22,
        "padding": 8, "content_padx": 6, "content_pady": (3, 2),
        "title_font": 10, "title_btn_w": 24, "title_btn_h": 20, "title_btn_font": 11,
        "chk_font": 9, "chk_w": 18, "chk_h": 14, "chk_box": 12,
        "pct_font": 9, "timer_font": 8,
        "bar_height": 6, "bar_radius": 3,
        "status_font": 8, "refresh_btn_w": 22, "refresh_btn_h": 18, "refresh_font": 10,
    },
    "medium": {
        "width": 260, "row_height": 50, "title_height": 30, "status_height": 26,
        "padding": 10, "content_padx": 8, "content_pady": (4, 3),
        "title_font": 12, "title_btn_w": 30, "title_btn_h": 24, "title_btn_font": 13,
        "chk_font": 11, "chk_w": 22, "chk_h": 18, "chk_box": 14,
        "pct_font": 11, "timer_font": 10,
        "bar_height": 8, "bar_radius": 4,
        "status_font": 9, "refresh_btn_w": 26, "refresh_btn_h": 20, "refresh_font": 12,
    },
    "large": {
        "width": 320, "row_height": 62, "title_height": 36, "status_height": 30,
        "padding": 12, "content_padx": 10, "content_pady": (5, 4),
        "title_font": 14, "title_btn_w": 36, "title_btn_h": 28, "title_btn_font": 15,
        "chk_font": 13, "chk_w": 26, "chk_h": 22, "chk_box": 16,
        "pct_font": 13, "timer_font": 12,
        "bar_height": 10, "bar_radius": 5,
        "status_font": 11, "refresh_btn_w": 30, "refresh_btn_h": 24, "refresh_font": 14,
    },
}


class ClaudeViewWidget(ctk.CTk):
    def __init__(self, config: Config):
        super().__init__()

        self.config = config
        self._last_data: UsageData | None = None
        self._drag_data = {"x": 0, "y": 0}
        self._setup_callback = None
        self._tray = None
        self._client: OAuthClient | None = None
        self._username: str | None = None
        self._title_label = None

        # Frameless, always on top, tool window (skip Alt+Tab & taskbar)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.config.opacity)

        # Hide from taskbar using Windows tool window style
        self.after(10, self._hide_from_taskbar)

        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window size from preset
        self._apply_size_preset()
        self.HEIGHT = self._calc_height()

        # Position
        self._apply_position()

        # Round corners via transparent bg (Windows 11)
        self.configure(fg_color="#1e1e2e")

        # Build UI
        self._build_ui()

        # Bind drag
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)

        # Right-click menu
        self._context_menu = self._build_context_menu()
        self.bind("<ButtonPress-3>", self._show_context_menu)

    def _hide_from_taskbar(self):
        """Hide window from taskbar using Win32 API (WS_EX_TOOLWINDOW)."""
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        # Re-show to apply style change
        self.withdraw()
        self.after(50, self.deiconify)

    def _apply_size_preset(self):
        p = UI_PRESETS.get(self.config.ui_size, UI_PRESETS["medium"])
        self._p = p
        self.WIDTH = p["width"]
        self.ROW_HEIGHT = p["row_height"]
        self.TITLE_HEIGHT = p["title_height"]
        self.STATUS_HEIGHT = p["status_height"]
        self.PADDING = p["padding"]

    def _calc_height(self) -> int:
        visible = sum([
            self.config.show_five_hour,
            self.config.show_seven_day,
            self.config.show_sonnet,
        ])
        visible = max(visible, 1)  # at least 1 row height
        return self.TITLE_HEIGHT + (self.ROW_HEIGHT * visible) + self.STATUS_HEIGHT + self.PADDING

    def _apply_position(self):
        if self.config.position_x == -1 or self.config.position_y == -1:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = screen_w - self.WIDTH - 20
            y = screen_h - self.HEIGHT - 60
        else:
            x = self.config.position_x
            y = self.config.position_y
        # Clamp to screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, min(x, screen_w - self.WIDTH))
        y = max(0, min(y, screen_h - self.HEIGHT))
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _build_ui(self):
        p = self._p
        # Title bar
        title_frame = ctk.CTkFrame(self, fg_color="#16162a", height=p["title_height"], corner_radius=0)
        title_frame.pack(fill="x", padx=0, pady=0)
        title_frame.pack_propagate(False)

        title_text = f" ✦ {self._username}" if self._username else " ✦ Claude"
        self._title_label = ctk.CTkLabel(
            title_frame, text=title_text, font=("Segoe UI", p["title_font"], "bold"),
            text_color="#cdd6f4", anchor="w"
        )
        self._title_label.pack(side="left", fill="x", expand=True)

        close_btn = ctk.CTkButton(
            title_frame, text="✕", width=p["title_btn_w"], height=p["title_btn_h"],
            fg_color="transparent", hover_color="#e74c3c",
            font=("Segoe UI", p["title_btn_font"]), text_color="#cdd6f4",
            command=self._minimize_to_tray,
        )
        close_btn.pack(side="right", padx=(0, 1))

        settings_btn = ctk.CTkButton(
            title_frame, text="⚙", width=p["title_btn_w"], height=p["title_btn_h"],
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", p["title_btn_font"]), text_color="#cdd6f4",
            command=self._open_settings,
        )
        settings_btn.pack(side="right")

        # Content area
        content = ctk.CTkFrame(self, fg_color="#1e1e2e")
        content.pack(fill="both", expand=True, padx=p["content_padx"], pady=p["content_pady"])

        # Usage rows (dynamic based on config) with inline checkboxes
        self.row_five_hour = None
        self.row_seven_day = None
        self.row_sonnet = None

        if self.config.show_five_hour:
            self.row_five_hour = self._create_usage_row(
                content, "5h", "show_five_hour")
        if self.config.show_seven_day:
            self.row_seven_day = self._create_usage_row(
                content, "7d", "show_seven_day")
        if self.config.show_sonnet:
            self.row_sonnet = self._create_usage_row(
                content, "Sonnet", "show_sonnet")

        # Status bar
        status_frame = ctk.CTkFrame(self, fg_color="#16162a", height=p["status_height"], corner_radius=0)
        status_frame.pack(fill="x", padx=0, pady=0)
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status_frame, text=" 대기 중...", font=("Segoe UI", p["status_font"]),
            text_color="#6c7086", anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        refresh_btn = ctk.CTkButton(
            status_frame, text="↻", width=p["refresh_btn_w"], height=p["refresh_btn_h"],
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", p["refresh_font"]), text_color="#6c7086",
            command=self._manual_refresh,
        )
        refresh_btn.pack(side="right", padx=(0, 2))

    def _create_usage_row(self, parent, label_text: str, config_key: str) -> dict:
        p = self._p
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(1, 0))

        # Top line: checkbox-label + percentage
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x")

        chk_var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(
            top, text=label_text, variable=chk_var,
            font=("Segoe UI", p["chk_font"]), text_color="#bac2de",
            fg_color="#89b4fa", hover_color="#74c7ec",
            border_color="#45475a", checkmark_color="#1e1e2e",
            width=p["chk_w"], height=p["chk_h"],
            checkbox_width=p["chk_box"], checkbox_height=p["chk_box"],
            command=lambda: self._on_row_toggle(config_key, chk_var),
        )
        chk.pack(side="left")

        pct_label = ctk.CTkLabel(
            top, text="—%", font=("Segoe UI", p["pct_font"], "bold"),
            text_color="#cdd6f4", anchor="e"
        )
        pct_label.pack(side="right")

        timer_label = ctk.CTkLabel(
            top, text="", font=("Segoe UI", p["timer_font"]),
            text_color="#7f849c", anchor="e"
        )
        timer_label.pack(side="right", padx=(0, 4))

        # Progress bar (compact)
        progress = ctk.CTkProgressBar(
            frame, height=p["bar_height"], corner_radius=p["bar_radius"],
            fg_color="#313244", progress_color="#2ecc71"
        )
        progress.pack(fill="x", pady=(1, 0))
        progress.set(0)

        return {
            "frame": frame,
            "progress": progress,
            "pct_label": pct_label,
            "timer_label": timer_label,
        }

    def _on_row_toggle(self, config_key: str, var: ctk.BooleanVar):
        """Handle checkbox toggle on a usage row."""
        value = var.get()
        # Prevent unchecking all
        visible = sum([
            self.config.show_five_hour,
            self.config.show_seven_day,
            self.config.show_sonnet,
        ])
        if not value and visible <= 1:
            var.set(True)  # revert
            return

        setattr(self.config, config_key, value)
        self.config.save()
        # Rebuild after short delay so checkbox animation finishes
        self.after(150, self.rebuild_ui)

    def _build_context_menu(self):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a", activeforeground="#cdd6f4",
                       font=("Segoe UI", 10))
        menu.add_command(label="지금 새로고침", command=self._manual_refresh)
        menu.add_command(label="설정", command=self._open_settings)
        menu.add_separator()
        menu.add_command(label="☕ 후원하기", command=self._open_donate)
        menu.add_separator()
        menu.add_command(label="종료", command=self._quit_app)
        return menu

    def _show_context_menu(self, event):
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    # --- Drag ---
    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        x = self.winfo_x() + (event.x - self._drag_data["x"])
        y = self.winfo_y() + (event.y - self._drag_data["y"])
        self.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        self.config.position = (self.winfo_x(), self.winfo_y())
        self.config.save()

    # --- Data update ---
    def set_client(self, client: OAuthClient):
        self._client = client

    def update_display(self, data: UsageData):
        self._last_data = data
        rows = [
            (self.row_five_hour, data.five_hour),
            (self.row_seven_day, data.seven_day),
            (self.row_sonnet, data.seven_day_sonnet),
        ]
        for row_widgets, tier in rows:
            if row_widgets is None:
                continue
            pct = tier.utilization
            color = get_usage_color(pct)
            row_widgets["progress"].set(pct / 100.0)
            row_widgets["progress"].configure(progress_color=color)
            row_widgets["pct_label"].configure(text=f"{pct:.0f}%")
            row_widgets["timer_label"].configure(text=format_countdown(tier.resets_at))

    def update_status(self, text: str):
        self.status_label.configure(text=f" {text}")

    def tick_countdowns(self):
        if self._last_data:
            rows = [
                (self.row_five_hour, self._last_data.five_hour),
                (self.row_seven_day, self._last_data.seven_day),
                (self.row_sonnet, self._last_data.seven_day_sonnet),
            ]
            for row_widgets, tier in rows:
                if row_widgets is None:
                    continue
                row_widgets["timer_label"].configure(
                    text=format_countdown(tier.resets_at)
                )
        self.after(1000, self.tick_countdowns)

    def start_refresh_loop(self):
        self._do_refresh()
        self.tick_countdowns()

    def _do_refresh(self):
        if self._client:
            self.update_status("갱신 중...")
            thread = threading.Thread(target=self._fetch_in_background, daemon=True)
            thread.start()

        interval_ms = self.config.refresh_interval_seconds * 1000
        self.after(interval_ms, self._do_refresh)

    def _fetch_in_background(self):
        # Fetch username on first successful call
        if self._username is None and self._client:
            profile = self._client.fetch_profile()
            if profile:
                account = profile.get("account", {})
                name = (
                    account.get("display_name")
                    or account.get("full_name")
                    or account.get("email", "").split("@")[0]
                )
                if name:
                    self._username = name
                    self.after(0, self._update_title)
        result = self._client.fetch_usage()
        self.after(0, lambda: self._on_fetch_complete(result))

    def _on_fetch_complete(self, result: ApiResult):
        if result.success and result.data:
            self.update_display(result.data)
            fetched_str = result.data.fetched_at.astimezone().strftime("%H:%M:%S")
            self.update_status(f"{fetched_str} 갱신됨")
        elif result.error == "no_credentials":
            self.update_status("Claude Code 로그인 필요")
        elif result.error == "token_refresh_failed":
            self.update_status("토큰 갱신 실패 - Claude Code 재로그인")
        elif result.error == "auth_expired":
            self.update_status("인증 만료 - Claude Code 재로그인")
        elif result.error == "network_error":
            self.update_status("네트워크 오류")
        else:
            self.update_status(f"오류: {result.error}")

    def _manual_refresh(self):
        if self._client:
            self.update_status("새로고침 중...")
            thread = threading.Thread(target=self._fetch_in_background, daemon=True)
            thread.start()

    def rebuild_ui(self):
        """Rebuild the widget UI after config changes (e.g. visibility toggles)."""
        # Destroy all children
        for child in self.winfo_children():
            child.destroy()

        # Re-apply size preset and recalculate
        self._apply_size_preset()
        self.HEIGHT = self._calc_height()

        # Reposition with new height
        x = self.winfo_x()
        y = self.winfo_y()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, min(x, screen_w - self.WIDTH))
        y = max(0, min(y, screen_h - self.HEIGHT))
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # Rebuild
        self._build_ui()

        # Re-create context menu
        self._context_menu = self._build_context_menu()

        # Re-apply taskbar hiding
        self._hide_from_taskbar()

        # Apply opacity
        self.attributes("-alpha", self.config.opacity)

        # Re-display last data if available
        if self._last_data:
            self.update_display(self._last_data)

    # --- Actions ---
    def _minimize_to_tray(self):
        self.withdraw()

    def _open_settings(self):
        if self._setup_callback:
            self._setup_callback()

    def _update_title(self):
        """Update title bar with username."""
        if self._title_label and self._username:
            self._title_label.configure(text=f" ✦ {self._username}")

    def _open_donate(self):
        from setup_dialog import DonateDialog
        DonateDialog(self)

    def _quit_app(self):
        if self._tray:
            self._tray.stop()
        self.destroy()

    def set_setup_callback(self, callback):
        self._setup_callback = callback

    def set_tray(self, tray):
        self._tray = tray
