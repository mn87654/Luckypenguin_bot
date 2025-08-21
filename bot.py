import os
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
async def award_referral_if_any(user: User, start_payload: str | None):
    if not start_payload:
        return
    try:
        ref_tg = int(start_payload)
    except Exception:
        return
    if ref_tg == user.tg_id:
        return
    async with SessionLocal() as session:
        res = await session.execute(select(Referral).where(Referral.referred_tg == user.tg_id))
        if res.scalar_one_or_none():
            return
        session.add(Referral(referrer_tg=ref_tg, referred_tg=user.tg_id, reward_given=True))
        res2 = await session.execute(select(User).where(User.tg_id == ref_tg))
        ref_user = res2.scalar_one_or_none()
        if ref_user:
            ref_user.coins += settings.REFERRAL_REWARD
        await session.commit()
        if ref_user:
            try:
                await bot.send_message(ref_tg, f"🐧 Your referral joined! +{settings.REFERRAL_REWARD} coins 💰")
            except Exception:
                pass

async def list_active_tasks() -> list[Task]:
    async with SessionLocal() as session:
        res = await session.execute(select(Task).where(Task.active == True).order_by(Task.id))
        return list(res.scalars())

async def get_task(task_id: int) -> Task | None:
    async with SessionLocal() as session:
        res = await session.execute(select(Task).where(Task.id == task_id))
        return res.scalar_one_or_none()

async def has_completed_today(user_id: int, task_id: int, date_key: str) -> bool:
    async with SessionLocal() as session:
        res = await session.execute(
            select(TaskCompletion).where(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.date_key == date_key,
            )
        )
        return res.scalar_one_or_none() is not None

async def complete_task_and_reward(user: User, task: Task, date_key: str):
    async with SessionLocal() as session:
        res_u = await session.execute(select(User).where(User.tg_id == user.tg_id))
        db_user = res_u.scalar_one()
        res = await session.execute(
            select(TaskCompletion).where(
                TaskCompletion.user_id == db_user.id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.date_key == date_key,
            )
        )
        if res.scalar_one_or_none():
            return db_user.coins
        session.add(TaskCompletion(user_id=db_user.id, task_id=task.id, date_key=date_key))
        db_user.coins += task.reward
        await session.commit()
        return db_user.coins

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

@rt.callback_query(F.data == "help")
async def cb_help(c: CallbackQuery):
    await c.answer()
    await c.message.edit_text(
        "❓ <b>How it works</b>\n"
        "1) Tap <b>Daily</b> once every 24h to claim your reward.\n"
        "2) Open <b>Tasks</b> → finish items → press <b>Check</b> to verify.\n"
        "3) <b>Invite friends</b> – share your personal link. When they start the bot, you earn coins.\n\n"
        "Anti-cheat: self-referrals blocked; join tasks verified via Telegram API.",
        reply_markup=main_kb()
    )

@rt.callback_query(F.data == "balance")
async def cb_balance(c: CallbackQuery):
    await c.answer()
    user = await get_or_create_user(c.from_user.id, c.from_user.username)
    await c.message.edit_text(f"💰 <b>Your coins:</b> {user.coins}", reply_markup=main_kb())

@rt.callback_query(F.data == "invite")
async def cb_invite(c: CallbackQuery):
    await c.answer()
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={c.from_user.id}"
    await c.message.edit_text(
        "👥 <b>Invite friends & earn</b>\n"
        f"Share your link:\n{link}\n\n"
        f"Reward per friend: +{settings.REFERRAL_REWARD} coins.",
        reply_markup=main_kb()
    )

@rt.callback_query(F.data == "tasks")
async def cb_tasks(c: CallbackQuery):
    await c.answer()
    tasks = await list_active_tasks()
    if not tasks:
        await c.message.edit_text("🧩 No tasks yet. Check back soon!", reply_markup=main_kb())
        return
    await c.message.edit_text("🧩 <b>Tasks</b>\nTap <i>Join/Open</i>, then press <b>Check</b>.", reply_markup=main_kb())
    for t in tasks:
        if t.type == "daily_checkin":
            continue
        descr = f"• {t.title} — <b>+{t.reward}</b>"
        await c.message.answer(descr, reply_markup=task_item_kb(t))

@rt.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    await c.answer()
    async with SessionLocal() as session:
        res = await session.execute(select(Task).where(Task.type == "daily_checkin"))
        daily = res.scalar_one()
    user = await get_or_create_user(c.from_user.id, c.from_user.username)
    day = today_key()
    if await has_completed_today(user.id, daily.id, day):
        await c.message.edit_text("🎁 You already claimed today. Come back in 24h!", reply_markup=main_kb())
        return
    new_balance = await complete_task_and_reward(user, daily, day)
    await c.message.edit_text(f"🎉 Daily reward received! +{daily.reward} coins\n"
                              f"💰 Balance: {new_balance}", reply_markup=main_kb())

@rt.callback_query(F.data.startswith("check:"))
async def cb_check(c: CallbackQuery):
    await c.answer("Checking…", show_alert=False)
    task_id = int(c.data.split(":")[1])
    task = await get_task(task_id)
    if not task or not task.active:
        await c.message.answer("This task is no longer active.")
        return

    user = await get_or_create_user(c.from_user.id, c.from_user.username)
    date_key = today_key() if task.is_daily else "ONCE"

    ok = False
    if task.type == "join_channel":
        channel = task.data.lstrip("@")
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user.tg_id)
            ok = member.status in ("member", "administrator", "creator")
        except Exception:
            ok = False
    elif task.type == "visit_link":
        ok = True

    if not ok:
        if task.type == "join_channel":
            await c.message.answer("I can't see you in the channel yet. Please join first and then press <b>Check</b> again.")
        else:
            await c.message.answer("Task not verified yet. Try again after completing.")
        return

    new_balance = await complete_task_and_reward(user, task, date_key)
    await c.message.answer(f"✅ Task completed: <b>{task.title}</b>\n+{task.reward} coins.\n💰 Balance: {new_balance}")

from admin import admin_rt
dp.include_router(admin_rt)

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
    app.router.add_get("/", lambda r: web.Response(text="Penguin Night bot is running."))
    return app

if __name__ == "__main__":
    app = build_app()
    web.run_app(app, host="0.0.0.0", port=settings.PORT)
