import os
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties

from settings import settings
from database import init_db, get_or_create_user, SessionLocal
from models import User, Task, TaskCompletion, Referral
from sqlalchemy import select, delete
from timeutil import today_key

# --- Bot & Dispatcher ---
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
rt = Router()
dp.include_router(rt)

# ---------- Keyboards ----------
def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily")],
        [InlineKeyboardButton(text="🧩 Tasks", callback_data="tasks")],
        [InlineKeyboardButton(text="👥 Invite friends", callback_data="invite")],
        [InlineKeyboardButton(text="💰 My Coins", callback_data="balance")],
        [InlineKeyboardButton(text="🕹 Open App", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}"))],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
    ])

def task_item_kb(task: Task) -> InlineKeyboardMarkup:
    buttons = []
    if task.type == "join_channel":
        url = f"https://t.me/{task.data.lstrip('@')}"
        buttons.append(InlineKeyboardButton(text="Join Channel", url=url))
        buttons.append(InlineKeyboardButton(text="✅ I joined (Check)", callback_data=f"check:{task.id}"))
    elif task.type == "visit_link":
        buttons.append(InlineKeyboardButton(text="Open Link", url=task.data))
        buttons.append(InlineKeyboardButton(text="✅ Done (Check)", callback_data=f"check:{task.id}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# ---------- Helpers ----------
# (unchanged referral, task fetching, completion helpers)
# ... [SAME AS BEFORE]

# ---------- User commands ----------
@rt.message(CommandStart())
async def cmd_start(message: Message):
    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await award_referral_if_any(user, payload)

    text = (
        "🌌 <b>Penguin Night</b>\n"
        "Welcome, explorer! The aurora is shining and our penguin needs your help.\n\n"
        "• Earn coins from <b>Daily</b> and <b>Tasks</b>\n"
        "• Invite friends to get bonus coins\n"
        "• Spend coins later on upgrades (coming soon)\n\n"
        "Choose an option below ⤵️"
    )
    await message.answer(text, reply_markup=main_kb())

# (keep all callbacks: help, balance, invite, tasks, daily, check as before)

from admin import admin_rt
dp.include_router(admin_rt)

# ---------- Web APIs for WebApp ----------
async def api_me(request: web.Request):
    tg_id = int(request.query.get("tg_id", 0))
    if not tg_id:
        return web.json_response({"error": "missing tg_id"}, status=400)
    user = await get_or_create_user(tg_id)
    return web.json_response({
        "coins": user.coins,
        "username": user.username,
    })

async def api_daily_claim(request: web.Request):
    tg_id = int(request.query.get("tg_id", 0))
    if not tg_id:
        return web.json_response({"error": "missing tg_id"}, status=400)
    async with SessionLocal() as session:
        res = await session.execute(select(Task).where(Task.type == "daily_checkin"))
        daily = res.scalar_one()
    user = await get_or_create_user(tg_id)
    day = today_key()
    if await has_completed_today(user.id, daily.id, day):
        return web.json_response({"message": "already claimed", "coins": user.coins})
    new_balance = await complete_task_and_reward(user, daily, day)
    return web.json_response({"message": "claimed", "coins": new_balance})

# ---------- Web server ----------
async def on_startup(app: web.Application):
    await init_db()
    url = settings.webhook_url()
    if url:
        try:
            await bot.set_webhook(url)
        except Exception:
            pass

async def on_shutdown(app: web.Application):
    await bot.session.close()

def build_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    SimpleRequestHandler(dispatcher=dp, bot=bot, webhook_path=settings.WEBHOOK_PATH).register(app, path=settings.WEBHOOK_PATH)

    # API endpoints
    app.router.add_get("/api/me", api_me)
    app.router.add_get("/api/daily/claim", api_daily_claim)

    # Serve React build (webapp/dist)
    app.router.add_static("/webapp", path="./webapp/dist", name="webapp")
    app.router.add_get("/", lambda r: web.Response(text="Penguin Night bot is running."))

    return app

if __name__ == "__main__":
    app = build_app()
    web.run_app(app, host="0.0.0.0", port=settings.PORT)
