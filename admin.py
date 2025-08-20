from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, delete
from database import SessionLocal
from models import Task, User
from settings import settings

admin_rt = Router()

def _is_admin(uid: int) -> bool:
    return uid in settings.ADMINS

@admin_rt.message(Command("setcoins"))
async def setcoins_cmd(m: Message):
    if not _is_admin(m.from_user.id):
        return
    # /setcoins <tg_id> <amount>
    try:
        _, tg, amount = m.text.split(maxsplit=2)
        tg_id = int(tg); amount = int(amount)
    except Exception:
        await m.reply("Usage: <code>/setcoins 123456789 5000</code>")
        return
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.tg_id == tg_id))
        user = res.scalar_one_or_none()
        if not user:
            await m.reply("User not found.")
            return
        user.coins = amount
        await session.commit()
    await m.reply(f"✅ Set {tg_id} coins = {amount}")

@admin_rt.message(Command("addchannel"))
async def addchannel_cmd(m: Message):
    if not _is_admin(m.from_user.id):
        return
    # /addchannel @username reward [daily yes/no] [title...]
    parts = m.text.split()
    if len(parts) < 3:
        await m.reply("Usage:\n<code>/addchannel @channel 100 daily yes Title of task</code>")
        return
    _, channel, reward, *rest = parts
    reward = int(reward)
    daily = False
    title = f"Join {channel}"
    if rest:
        # allow "daily yes/no"
        if rest[0].lower() == "daily" and len(rest) >= 2:
            daily = rest[1].lower() in ("yes", "y", "true", "1")
            title = " ".join(rest[2:]) or title
        else:
            title = " ".join(rest)
    async with SessionLocal() as session:
        t = Task(type="join_channel", title=title, data=channel, reward=reward, is_daily=daily, active=True)
        session.add(t)
        await session.commit()
    await m.reply(f"✅ Task added (join_channel) → {title} (+{reward}) daily={daily}")

@admin_rt.message(Command("addlink"))
async def addlink_cmd(m: Message):
    if not _is_admin(m.from_user.id):
        return
    # /addlink https://link 200 [daily yes/no] [Title...]
    parts = m.text.split()
    if len(parts) < 3:
        await m.reply("Usage:\n<code>/addlink https://example.com 200 daily no Visit our site</code>")
        return
    _, url, reward, *rest = parts
    reward = int(reward)
    daily = False
    title = "Visit link"
    if rest:
        if rest[0].lower() == "daily" and len(rest) >= 2:
            daily = rest[1].lower() in ("yes", "y", "true", "1")
            title = " ".join(rest[2:]) or title
        else:
            title = " ".join(rest)
    async with SessionLocal() as session:
        t = Task(type="visit_link", title=title, data=url, reward=reward, is_daily=daily, active=True)
        session.add(t)
        await session.commit()
    await m.reply(f"✅ Task added (visit_link) → {title} (+{reward}) daily={daily}")

@admin_rt.message(Command("removetask"))
async def removetask_cmd(m: Message):
    if not _is_admin(m.from_user.id):
        return
    # /removetask <task_id>
    parts = m.text.split()
    if len(parts) != 2:
        await m.reply("Usage: <code>/removetask 12</code>")
        return
    tid = int(parts[1])
    async with SessionLocal() as session:
        await session.execute(delete(Task).where(Task.id == tid))
        await session.commit()
    await m.reply(f"🗑️ Task {tid} removed.")
