import os
import customtkinter as ctk
from PIL import Image
from config import Config
from api_client import OAuthClient

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


class SetupDialog(ctk.CTkToplevel):
    def __init__(self, parent, config: Config, on_complete=None):
        super().__init__(parent)

        self._parent = parent
        self.config = config
        self.on_complete = on_complete

        self.title("ClaudeMonitor 설정")
        self.geometry("400x510")
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
            self, text="ClaudeMonitor 설정",
            font=("Segoe UI", 16, "bold"), text_color="#cdd6f4"
        ).pack(pady=(20, 8))

        # Token status + login/logout button
        auth_frame = ctk.CTkFrame(self, fg_color="transparent")
        auth_frame.pack(pady=(0, 8), padx=24, fill="x")

        self._client_ref = self._parent._client if hasattr(self._parent, '_client') else OAuthClient()
        self._is_authenticated = bool(self._client_ref and self._client_ref.has_credentials)

        self._auth_indicator = ctk.CTkLabel(
            auth_frame,
            text="● 인증됨" if self._is_authenticated else "● 미인증",
            font=("Segoe UI", 11),
            text_color="#a6e3a1" if self._is_authenticated else "#f38ba8"
        )
        self._auth_indicator.pack(side="left")

        if self._is_authenticated:
            self._login_btn = ctk.CTkButton(
                auth_frame, text="로그아웃", width=90, height=28,
                fg_color="#45475a", hover_color="#585b70",
                font=("Segoe UI", 10, "bold"), text_color="#cdd6f4",
                command=self._do_logout,
            )
        else:
            self._login_btn = ctk.CTkButton(
                auth_frame, text="Claude 로그인", width=110, height=28,
                fg_color="#89b4fa", hover_color="#74c7ec",
                font=("Segoe UI", 10, "bold"), text_color="#1e1e2e",
                command=self._start_login,
            )
        self._login_btn.pack(side="right")

        self._auth_status = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 9), text_color="#a6adc8"
        )
        self._auth_status.pack(pady=(0, 4))

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

        # UI Size
        size_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        size_frame.pack(pady=(10, 4), padx=16, fill="x")

        ctk.CTkLabel(
            size_frame, text="위젯 크기:",
            font=("Segoe UI", 11), text_color="#bac2de"
        ).pack(side="left")

        size_map = {"small": "소", "medium": "중", "large": "대"}
        current_label = size_map.get(self.config.ui_size, "중")
        self.size_var = ctk.StringVar(value=current_label)
        self.size_menu = ctk.CTkSegmentedButton(
            size_frame, values=["소", "중", "대"],
            variable=self.size_var,
            font=("Segoe UI", 10),
            selected_color="#89b4fa", selected_hover_color="#74c7ec",
            unselected_color="#313244", unselected_hover_color="#45475a",
            text_color="#1e1e2e", text_color_disabled="#6c7086",
            width=120, height=26,
        )
        self.size_menu.pack(side="right")

        # Refresh interval
        interval_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        interval_frame.pack(pady=(4, 4), padx=16, fill="x")

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
        self.status_label.pack(pady=(0, 4))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 4))

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

        # Donate button
        ctk.CTkButton(
            self, text="☕ 후원하기", width=120, height=28,
            fg_color="#45475a", hover_color="#585b70",
            font=("Segoe UI", 10), text_color="#cdd6f4",
            command=self._open_donate,
        ).pack(pady=(0, 10))

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

        # Size mapping
        size_label_map = {"소": "small", "중": "medium", "대": "large"}
        new_size = size_label_map.get(self.size_var.get(), "medium")

        # Check if rebuild needed
        needs_rebuild = (
            self.config.show_five_hour != show_five or
            self.config.show_seven_day != show_seven or
            self.config.show_sonnet != show_sonnet or
            self.config.ui_size != new_size
        )

        self.config.refresh_interval_seconds = interval
        self.config.opacity = opacity
        self.config.show_five_hour = show_five
        self.config.show_seven_day = show_seven
        self.config.show_sonnet = show_sonnet
        self.config.ui_size = new_size
        self.config.save()

        if self.on_complete:
            self.on_complete()

        # If layout changed, close dialog first then rebuild widget
        if needs_rebuild:
            self.destroy()
            self._parent.rebuild_ui()
            return

        # Just apply opacity
        self._parent.attributes("-alpha", opacity)
        self.status_label.configure(text="저장됨", text_color="#a6e3a1")

    def _start_login(self):
        self._login_btn.configure(state="disabled", text="인증 중...")
        self._auth_status.configure(text="브라우저에서 로그인해주세요...", text_color="#f9e2af")

        if self._client_ref:
            self._client_ref.start_login(lambda ok, msg: self.after(0, lambda: self._on_login_done(ok, msg)))

    def _on_login_done(self, success: bool, message: str):
        if success:
            self._auth_status.configure(text="✓ " + message, text_color="#a6e3a1")
            self._auth_indicator.configure(text="● 인증됨", text_color="#a6e3a1")
            # Switch to logout button
            auth_frame = self._auth_indicator.master
            self._login_btn.destroy()
            self._login_btn = ctk.CTkButton(
                auth_frame, text="로그아웃", width=90, height=28,
                fg_color="#45475a", hover_color="#585b70",
                font=("Segoe UI", 10, "bold"), text_color="#cdd6f4",
                command=self._do_logout,
            )
            self._login_btn.pack(side="right")
            # Trigger refresh
            if hasattr(self._parent, '_manual_refresh'):
                self._parent._manual_refresh()
        else:
            self._auth_status.configure(text=message, text_color="#f38ba8")
            self._login_btn.configure(state="normal", text="Claude 로그인")

    def _do_logout(self):
        if self._client_ref:
            self._client_ref.logout()
        self._auth_indicator.configure(text="● 미인증", text_color="#f38ba8")
        self._auth_status.configure(text="로그아웃됨", text_color="#a6adc8")
        # Reset username in widget
        if hasattr(self._parent, '_username'):
            self._parent._username = None
            if hasattr(self._parent, '_update_title'):
                self._parent._title_label.configure(text=" ✦ Claude")
        # Switch to login button
        self._login_btn.destroy()
        self._login_btn = ctk.CTkButton(
            self._auth_indicator.master,
            text="Claude 로그인", width=110, height=28,
            fg_color="#89b4fa", hover_color="#74c7ec",
            font=("Segoe UI", 10, "bold"), text_color="#1e1e2e",
            command=self._start_login,
        )
        self._login_btn.pack(side="right")

    def _open_donate(self):
        DonateDialog(self)

    def _on_close(self):
        self.destroy()


class DonateDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("☕ 후원하기")
        self.resizable(False, False)
        self.grab_set()
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e2e")

        self._build_ui()

        # Center on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.lift()
        self.focus_force()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="☕ 커피 한 잔 후원하기",
            font=("Segoe UI", 14, "bold"), text_color="#cdd6f4"
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            self, text="카카오페이로 스캔해주세요",
            font=("Segoe UI", 10), text_color="#a6adc8"
        ).pack(pady=(0, 8))

        # QR image
        qr_path = os.path.join(ASSETS_DIR, "donate_qr.png")
        if os.path.exists(qr_path):
            pil_img = Image.open(qr_path)
            # Scale to fit dialog (max 250px wide)
            ratio = min(250 / pil_img.width, 350 / pil_img.height)
            new_w = int(pil_img.width * ratio)
            new_h = int(pil_img.height * ratio)
            self._qr_image = ctk.CTkImage(
                light_image=pil_img, dark_image=pil_img,
                size=(new_w, new_h)
            )
            ctk.CTkLabel(self, image=self._qr_image, text="").pack(pady=(0, 8))
        else:
            ctk.CTkLabel(
                self, text="QR 이미지 없음",
                font=("Segoe UI", 11), text_color="#f38ba8"
            ).pack(pady=(20, 20))

        ctk.CTkButton(
            self, text="닫기", width=80,
            fg_color="transparent", hover_color="#45475a",
            font=("Segoe UI", 11), text_color="#6c7086",
            command=self.destroy,
        ).pack(pady=(0, 12))
