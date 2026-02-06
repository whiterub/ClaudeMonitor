import threading
from datetime import datetime, timezone

import customtkinter as ctk

from api_client import UsageData, ApiResult, OAuthClient
from config import Config
from utils import get_usage_color, format_countdown


class ClaudeViewWidget(ctk.CTk):
    def __init__(self, config: Config):
        super().__init__()

        self.config = config
        self._last_data: UsageData | None = None
        self._drag_data = {"x": 0, "y": 0}
        self._setup_callback = None
        self._tray = None
        self._client: OAuthClient | None = None

        # Frameless, always on top, tool window (skip Alt+Tab)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.config.opacity)

        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window size
        self.WIDTH = 300
        self.ROW_HEIGHT = 46  # height per usage row (compact)
        self.TITLE_HEIGHT = 30
        self.STATUS_HEIGHT = 28
        self.PADDING = 8
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
        # Title bar
        title_frame = ctk.CTkFrame(self, fg_color="#16162a", height=30, corner_radius=0)
        title_frame.pack(fill="x", padx=0, pady=0)
        title_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            title_frame, text="  ✦ ClaudeView", font=("Segoe UI", 12, "bold"),
            text_color="#cdd6f4", anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True)

        close_btn = ctk.CTkButton(
            title_frame, text="✕", width=30, height=26,
            fg_color="transparent", hover_color="#e74c3c",
            font=("Segoe UI", 13), text_color="#cdd6f4",
            command=self._minimize_to_tray,
        )
        close_btn.pack(side="right", padx=(0, 2))

        settings_btn = ctk.CTkButton(
            title_frame, text="⚙", width=30, height=26,
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", 13), text_color="#cdd6f4",
            command=self._open_settings,
        )
        settings_btn.pack(side="right")

        # Content area
        content = ctk.CTkFrame(self, fg_color="#1e1e2e")
        content.pack(fill="both", expand=True, padx=8, pady=(4, 2))

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
        status_frame = ctk.CTkFrame(self, fg_color="#16162a", height=28, corner_radius=0)
        status_frame.pack(fill="x", padx=0, pady=0)
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status_frame, text="  대기 중...", font=("Segoe UI", 9),
            text_color="#6c7086", anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        refresh_btn = ctk.CTkButton(
            status_frame, text="↻", width=28, height=20,
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", 12), text_color="#6c7086",
            command=self._manual_refresh,
        )
        refresh_btn.pack(side="right", padx=(0, 4))

    def _create_usage_row(self, parent, label_text: str, config_key: str) -> dict:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(1, 0))

        # Top line: checkbox-label + timer + percentage
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x")

        chk_var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(
            top, text=label_text, variable=chk_var,
            font=("Segoe UI", 10), text_color="#bac2de",
            fg_color="#89b4fa", hover_color="#74c7ec",
            border_color="#45475a", checkmark_color="#1e1e2e",
            width=20, height=16, checkbox_width=14, checkbox_height=14,
            command=lambda: self._on_row_toggle(config_key, chk_var),
        )
        chk.pack(side="left")

        pct_label = ctk.CTkLabel(
            top, text="—%", font=("Segoe UI", 10, "bold"),
            text_color="#cdd6f4", anchor="e"
        )
        pct_label.pack(side="right")

        timer_label = ctk.CTkLabel(
            top, text="", font=("Segoe UI", 9),
            text_color="#7f849c", anchor="e"
        )
        timer_label.pack(side="right", padx=(0, 6))

        # Progress bar (compact)
        progress = ctk.CTkProgressBar(
            frame, height=8, corner_radius=4,
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
        self.status_label.configure(text=f"  {text}")

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

        # Recalculate height
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

    def _quit_app(self):
        if self._tray:
            self._tray.stop()
        self.destroy()

    def set_setup_callback(self, callback):
        self._setup_callback = callback

    def set_tray(self, tray):
        self._tray = tray
