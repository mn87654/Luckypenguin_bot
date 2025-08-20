import os
from dataclasses import dataclass

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
    ADMINS: set[int] = _admins_set(os.environ.get("ADMINS", ""))
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./penguin.db")
    DAILY_REWARD: int = int(os.environ.get("DAILY_REWARD", "100"))
    REFERRAL_REWARD: int = int(os.environ.get("REFERRAL_REWARD", "200"))
    TIMEZONE: str = os.environ.get("TIMEZONE", "UTC")
    WEBHOOK_BASE_URL: str = os.environ.get("WEBHOOK_BASE_URL", "")  # e.g. https://your-render.onrender.com
    WEBHOOK_PATH: str = os.environ.get("WEBHOOK_PATH", "/webhook")
    PORT: int = int(os.environ.get("PORT", "10000"))  # Render sets this

    def webhook_url(self) -> str | None:
        # Render auto-adds RENDER_EXTERNAL_HOSTNAME
        if not self.WEBHOOK_BASE_URL:
            host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
            if host:
                return f"https://{host}{self.WEBHOOK_PATH}"
            return None
        return f"{self.WEBHOOK_BASE_URL}{self.WEBHOOK_PATH}"

settings = Settings()
