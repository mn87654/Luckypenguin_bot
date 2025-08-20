from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func
from models import Base, User, Task, TaskCompletion, Referral
from settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure a hidden "daily_checkin" task exists
    async with SessionLocal() as session:
        res = await session.execute(select(Task).where(Task.type == "daily_checkin"))
        t = res.scalar_one_or_none()
        if not t:
            t = Task(type="daily_checkin", title="Daily Check-in", data="daily", reward=settings.DAILY_REWARD, is_daily=True, active=True)
            session.add(t)
            await session.commit()

async def get_or_create_user(tg_id: int, username: Optional[str]) -> User:
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.tg_id == tg_id))
        user = res.scalar_one_or_none()
        if user:
            user.username = username
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user
        user = User(tg_id=tg_id, username=username, coins=0)
        session.add(user)
        await session.commit()
        return user

async def add_coins(tg_id: int, delta: int) -> int:
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.tg_id == tg_id))
        user = res.scalar_one()
        user.coins += delta
        user.updated_at = datetime.utcnow()
        await session.commit()
        return user.coins
