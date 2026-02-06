import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


CREDENTIALS_PATH = os.path.join(os.path.expanduser("~"), ".claude", ".credentials.json")
TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
OAUTH_SCOPES = "org:create_api_key user:profile user:inference"
PROFILE_URL = "https://api.anthropic.com/api/oauth/profile"


@dataclass
class UsageTier:
    utilization: float
    resets_at: Optional[datetime]


@dataclass
class UsageData:
    five_hour: UsageTier
    seven_day: UsageTier
    seven_day_sonnet: UsageTier
    fetched_at: datetime


@dataclass
class ApiResult:
    success: bool
    data: Optional[UsageData]
    error: Optional[str]


def _parse_tier(raw: Optional[dict]) -> UsageTier:
    if raw is None:
        return UsageTier(utilization=0, resets_at=None)
    utilization = float(raw.get("utilization", 0))
    resets_at_str = raw.get("resets_at")
    resets_at = None
    if resets_at_str:
        try:
            resets_at = datetime.fromisoformat(resets_at_str)
        except ValueError:
            pass
    return UsageTier(utilization=utilization, resets_at=resets_at)


def _parse_usage(raw: dict) -> UsageData:
    return UsageData(
        five_hour=_parse_tier(raw.get("five_hour")),
        seven_day=_parse_tier(raw.get("seven_day")),
        seven_day_sonnet=_parse_tier(raw.get("seven_day_sonnet")),
        fetched_at=datetime.now(timezone.utc),
    )


class OAuthClient:
    """Manages Claude Code OAuth tokens and fetches usage data."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = threading.Lock()
        self._load_credentials()

    @property
    def has_credentials(self) -> bool:
        return self._refresh_token is not None

    def logout(self):
        """Clear stored credentials."""
        self._access_token = None
        self._refresh_token = None
        self._expires_at = 0
        try:
            if os.path.exists(CREDENTIALS_PATH):
                with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.pop("claudeAiOauth", None)
                with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=None, ensure_ascii=False)
        except Exception:
            pass

    def _load_credentials(self):
        if not os.path.exists(CREDENTIALS_PATH):
            return
        try:
            with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            oauth = data.get("claudeAiOauth", {})
            self._access_token = oauth.get("accessToken")
            self._refresh_token = oauth.get("refreshToken")
            expires_at = oauth.get("expiresAt", 0)
            self._expires_at = expires_at / 1000.0 if expires_at > 1e12 else expires_at
        except Exception:
            pass

    def _save_credentials(self):
        try:
            # Read existing file to preserve other keys
            existing = {}
            if os.path.exists(CREDENTIALS_PATH):
                with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            existing["claudeAiOauth"] = {
                "accessToken": self._access_token,
                "refreshToken": self._refresh_token,
                "expiresAt": int(self._expires_at * 1000),
                "scopes": existing.get("claudeAiOauth", {}).get("scopes", []),
                "subscriptionType": existing.get("claudeAiOauth", {}).get("subscriptionType", ""),
                "rateLimitTier": existing.get("claudeAiOauth", {}).get("rateLimitTier", ""),
            }

            os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)
            with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=None, ensure_ascii=False)
        except Exception:
            pass

    def _token_expired(self) -> bool:
        return time.time() >= self._expires_at - 60  # 1 minute buffer

    def _do_refresh(self) -> bool:
        if not self._refresh_token:
            return False
        try:
            payload = json.dumps({
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": self._refresh_token,
            }).encode("utf-8")

            req = Request(TOKEN_URL, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "claude-code/2.0.32")

            with urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            self._access_token = result["access_token"]
            self._refresh_token = result.get("refresh_token", self._refresh_token)
            expires_in = result.get("expires_in", 28800)
            self._expires_at = time.time() + expires_in
            self._save_credentials()
            return True
        except Exception:
            return False

    def _ensure_token(self) -> bool:
        with self._lock:
            if not self._access_token or self._token_expired():
                return self._do_refresh()
            return True

    def fetch_usage(self) -> ApiResult:
        if not self.has_credentials:
            return ApiResult(success=False, data=None, error="no_credentials")

        if not self._ensure_token():
            return ApiResult(success=False, data=None, error="token_refresh_failed")

        try:
            req = Request(USAGE_URL)
            req.add_header("Authorization", f"Bearer {self._access_token}")
            req.add_header("anthropic-beta", "oauth-2025-04-20")

            with urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            return ApiResult(success=True, data=_parse_usage(raw), error=None)
        except HTTPError as e:
            if e.code == 401:
                # Token expired mid-flight, try refresh once
                with self._lock:
                    if self._do_refresh():
                        try:
                            req = Request(USAGE_URL)
                            req.add_header("Authorization", f"Bearer {self._access_token}")
                            req.add_header("anthropic-beta", "oauth-2025-04-20")
                            with urlopen(req, timeout=15) as resp:
                                raw = json.loads(resp.read().decode("utf-8"))
                            return ApiResult(success=True, data=_parse_usage(raw), error=None)
                        except Exception:
                            pass
                return ApiResult(success=False, data=None, error="auth_expired")
            return ApiResult(success=False, data=None, error=f"http_{e.code}")
        except URLError:
            return ApiResult(success=False, data=None, error="network_error")
        except Exception as e:
            return ApiResult(success=False, data=None, error=str(e))

    def fetch_profile(self) -> Optional[dict]:
        """Fetch user profile. Returns dict with 'name', 'email' etc., or None."""
        if not self.has_credentials:
            return None
        if not self._ensure_token():
            return None
        try:
            req = Request(PROFILE_URL)
            req.add_header("Authorization", f"Bearer {self._access_token}")
            req.add_header("User-Agent", "claude-code/2.0.32")
            req.add_header("anthropic-beta", "oauth-2025-04-20")
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    # --- OAuth Login Flow ---
    def start_login(self, on_complete: Callable[[bool, str], None]):
        """Start OAuth login flow in background thread.
        on_complete(success: bool, message: str) called on completion."""
        thread = threading.Thread(
            target=self._login_flow, args=(on_complete,), daemon=True
        )
        thread.start()

    def _login_flow(self, on_complete: Callable[[bool, str], None]):
        try:
            # 1. Generate PKCE code_verifier and code_challenge
            verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
            digest = hashlib.sha256(verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

            # Separate state parameter for CSRF protection
            state = secrets.token_urlsafe(32)

            # 2. Start local callback server
            server, port = self._start_callback_server()

            redirect_uri = f"http://localhost:{port}/callback"

            # 3. Build authorization URL
            params = {
                "client_id": CLIENT_ID,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": OAUTH_SCOPES,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": state,
            }
            auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"

            # 4. Open browser
            webbrowser.open(auth_url)

            # 5. Wait for callback (timeout 120s)
            # Handle multiple requests (browser may send favicon, etc.)
            server.auth_code = None
            deadline = time.time() + 120
            while time.time() < deadline:
                server.timeout = max(1, deadline - time.time())
                server.handle_request()
                if getattr(server, "auth_code", None):
                    break
            server.server_close()

            auth_code = getattr(server, "auth_code", None)
            if not auth_code:
                on_complete(False, "인증 시간 초과 또는 취소됨")
                return

            # 6. Exchange code for tokens
            payload = json.dumps({
                "code": auth_code,
                "state": state,
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            }).encode("utf-8")

            req = Request(TOKEN_URL, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "claude-code/2.0.32")

            with urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            self._access_token = result["access_token"]
            self._refresh_token = result.get("refresh_token")
            expires_in = result.get("expires_in", 28800)
            self._expires_at = time.time() + expires_in
            self._save_credentials()

            on_complete(True, "로그인 성공!")
        except HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            on_complete(False, f"로그인 실패: HTTP {e.code} - {body[:200]}")
        except Exception as e:
            on_complete(False, f"로그인 실패: {e}")

    def _start_callback_server(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                # Only process /callback path
                if parsed.path == "/callback":
                    query = parse_qs(parsed.query)
                    code = query.get("code", [None])[0]
                    if code:
                        self.server.auth_code = code
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        "<html><body style='font-family:sans-serif;text-align:center;"
                        "padding:60px;background:#1e1e2e;color:#cdd6f4'>"
                        "<h2>✦ 인증 완료!</h2>"
                        "<p>이 탭을 닫아도 됩니다.</p>"
                        "</body></html>".encode("utf-8")
                    )
                else:
                    # Ignore favicon and other requests
                    self.send_response(204)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # suppress logs

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        return server, port
