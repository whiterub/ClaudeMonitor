import customtkinter as ctk
from config import Config
from api_client import OAuthClient


class SetupDialog(ctk.CTkToplevel):
    def __init__(self, parent, config: Config, on_complete=None):
        super().__init__(parent)

        self._parent = parent
        self.config = config
        self.on_complete = on_complete

        self.title("ClaudeView 설정")
        self.geometry("400x420")
        self.resizable(False, False)
        self.grab_set()
        self.attributes("-topmost", True)

        # Center on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.configure(fg_color="#1e1e2e")
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self, text="ClaudeView 설정",
            font=("Segoe UI", 16, "bold"), text_color="#cdd6f4"
        ).pack(pady=(20, 8))

        # Token status
        client = OAuthClient()
        if client.has_credentials:
            status_text = "Claude Code 인증: 연결됨"
            status_color = "#a6e3a1"
        else:
            status_text = "Claude Code 인증: 없음 (터미널에서 claude login 실행)"
            status_color = "#f38ba8"

        ctk.CTkLabel(
            self, text=status_text,
            font=("Segoe UI", 11), text_color=status_color
        ).pack(pady=(0, 12))

        # --- Display items section ---
        display_frame = ctk.CTkFrame(self, fg_color="#16162a", corner_radius=8)
        display_frame.pack(pady=(0, 8), padx=24, fill="x")

        ctk.CTkLabel(
            display_frame, text="표시 항목",
            font=("Segoe UI", 11, "bold"), text_color="#bac2de",
            anchor="w"
        ).pack(pady=(10, 4), padx=16, fill="x")

        self.chk_five_hour_var = ctk.BooleanVar(value=self.config.show_five_hour)
        ctk.CTkCheckBox(
            display_frame, text="5시간 세션",
            variable=self.chk_five_hour_var,
            font=("Segoe UI", 11), text_color="#cdd6f4",
            fg_color="#89b4fa", hover_color="#74c7ec",
            border_color="#45475a", checkmark_color="#1e1e2e",
        ).pack(pady=(0, 2), padx=24, anchor="w")

        self.chk_seven_day_var = ctk.BooleanVar(value=self.config.show_seven_day)
        ctk.CTkCheckBox(
            display_frame, text="주간 전체",
            variable=self.chk_seven_day_var,
            font=("Segoe UI", 11), text_color="#cdd6f4",
            fg_color="#89b4fa", hover_color="#74c7ec",
            border_color="#45475a", checkmark_color="#1e1e2e",
        ).pack(pady=(0, 2), padx=24, anchor="w")

        self.chk_sonnet_var = ctk.BooleanVar(value=self.config.show_sonnet)
        ctk.CTkCheckBox(
            display_frame, text="Sonnet 주간",
            variable=self.chk_sonnet_var,
            font=("Segoe UI", 11), text_color="#cdd6f4",
            fg_color="#89b4fa", hover_color="#74c7ec",
            border_color="#45475a", checkmark_color="#1e1e2e",
        ).pack(pady=(0, 10), padx=24, anchor="w")

        # --- Settings section ---
        settings_frame = ctk.CTkFrame(self, fg_color="#16162a", corner_radius=8)
        settings_frame.pack(pady=(0, 8), padx=24, fill="x")

        # Refresh interval
        interval_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        interval_frame.pack(pady=(10, 4), padx=16, fill="x")

        ctk.CTkLabel(
            interval_frame, text="갱신 주기 (초):",
            font=("Segoe UI", 11), text_color="#bac2de"
        ).pack(side="left")

        self.interval_entry = ctk.CTkEntry(
            interval_frame, width=60, height=28,
            font=("Segoe UI", 11),
            fg_color="#313244", border_color="#45475a",
            text_color="#cdd6f4"
        )
        self.interval_entry.pack(side="right")
        self.interval_entry.insert(0, str(self.config.refresh_interval_seconds))

        # Opacity
        opacity_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        opacity_frame.pack(pady=(4, 10), padx=16, fill="x")

        ctk.CTkLabel(
            opacity_frame, text="투명도 (0.3~1.0):",
            font=("Segoe UI", 11), text_color="#bac2de"
        ).pack(side="left")

        self.opacity_entry = ctk.CTkEntry(
            opacity_frame, width=60, height=28,
            font=("Segoe UI", 11),
            fg_color="#313244", border_color="#45475a",
            text_color="#cdd6f4"
        )
        self.opacity_entry.pack(side="right")
        self.opacity_entry.insert(0, str(self.config.opacity))

        # Status
        self.status_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 10), text_color="#a6adc8"
        )
        self.status_label.pack(pady=(0, 6))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))

        ctk.CTkButton(
            btn_frame, text="저장", width=100,
            fg_color="#89b4fa", hover_color="#74c7ec",
            font=("Segoe UI", 11, "bold"), text_color="#1e1e2e",
            command=self._save,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="닫기", width=80,
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", 11), text_color="#6c7086",
            command=self._on_close,
        ).pack(side="left", padx=8)

    def _save(self):
        try:
            interval = int(self.interval_entry.get().strip())
            interval = max(5, min(300, interval))
        except ValueError:
            interval = 30

        try:
            opacity = float(self.opacity_entry.get().strip())
            opacity = max(0.3, min(1.0, opacity))
        except ValueError:
            opacity = 0.9

        # At least one item must be visible
        show_five = self.chk_five_hour_var.get()
        show_seven = self.chk_seven_day_var.get()
        show_sonnet = self.chk_sonnet_var.get()
        if not (show_five or show_seven or show_sonnet):
            self.status_label.configure(text="최소 1개 항목을 선택하세요", text_color="#f38ba8")
            return

        # Check if visibility changed
        visibility_changed = (
            self.config.show_five_hour != show_five or
            self.config.show_seven_day != show_seven or
            self.config.show_sonnet != show_sonnet
        )

        self.config.refresh_interval_seconds = interval
        self.config.opacity = opacity
        self.config.show_five_hour = show_five
        self.config.show_seven_day = show_seven
        self.config.show_sonnet = show_sonnet
        self.config.save()

        if self.on_complete:
            self.on_complete()

        # If visibility changed, rebuild the widget UI
        if visibility_changed:
            self._parent.rebuild_ui()
        else:
            # Just apply opacity
            self._parent.attributes("-alpha", opacity)

        self.status_label.configure(text="저장됨", text_color="#a6e3a1")

    def _on_close(self):
        self.destroy()
