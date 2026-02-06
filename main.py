import ctypes
import sys
import os

# DPI awareness for crisp rendering on high-DPI displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Ensure the script's directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from widget import ClaudeViewWidget
from tray import TrayManager
from setup_dialog import SetupDialog
from api_client import OAuthClient


def main():
    config = Config.load()

    # Create OAuth client (reads ~/.claude/.credentials.json)
    client = OAuthClient()

    # Create main widget
    app = ClaudeViewWidget(config)
    app.set_client(client)

    if not client.has_credentials:
        app.update_status("Claude Code 로그인 필요 (claude login)")
    else:
        app.update_status("연결 중...")

    # Setup callback for opening settings dialog
    def open_settings():
        dialog = SetupDialog(app, config, on_complete=lambda: _on_settings_saved())
        dialog.focus()

    def _on_settings_saved():
        new_config = Config.load()
        app.config = new_config
        app.update_status("설정 저장됨")

    app.set_setup_callback(open_settings)

    # Start tray
    tray = TrayManager(app)
    tray.start()
    app.set_tray(tray)

    # Start refresh loop
    app.start_refresh_loop()

    # Run
    app.mainloop()


if __name__ == "__main__":
    main()
