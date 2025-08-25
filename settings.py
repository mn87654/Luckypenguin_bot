import os
from dataclasses import dataclass, field

def _admins_set(val: str) -> set[int]:
    vals = [v for v in val.replace(" ", "").split(",") if v]
    out = set()
    for v in vals:
        try:
            out.add(int(v))
        except ValueError:
            pass
    return out

@dataclass
class Settings:
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    ADMINS: set[int] = field(default_factory=set)
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./penguin.db")
    DAILY_REWARD: int = int(os.environ.get("DAILY_REWARD", "100"))
    REFERRAL_REWARD: int = int(os.environ.get("REFERRAL_REWARD", "200"))
    TIMEZONE: str = os.environ.get("TIMEZONE", "UTC")
    WEBHOOK_BASE_URL: str = os.environ.get("WEBHOOK_BASE_URL", "")
    WEBHOOK_PATH: str = os.environ.get("WEBHOOK_PATH", "/webhook")
    WEBAPP_PATH: str = os.environ.get("WEBAPP_PATH", "/app/webapp/dist")  # path to React build folder
    PORT: int = int(os.environ.get("PORT", "10000"))  # Render sets this

    def __post_init__(self):
        admins_env = os.environ.get("ADMINS", "")
        if admins_env:
            self.ADMINS = _admins_set(admins_env)

    def webhook_url(self) -> str | None:
        """Return the full webhook URL for Telegram bot."""
        if not self.WEBHOOK_BASE_URL:
            host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
            if host:
                return f"https://{host}{self.WEBHOOK_PATH}"
            return None
        return f"{self.WEBHOOK_BASE_URL}{self.WEBHOOK_PATH}"

    def webapp_url(self) -> str | None:
        """Return the full public URL to the React webapp."""
        host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
        base = self.WEBHOOK_BASE_URL or (f"https://{host}" if host else None)
        return f"{base}{self.WEBAPP_PATH}" if base else None

settings = Settings()
