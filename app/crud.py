from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, auth


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str):
    hashed = auth.hash_password(password)
    user = models.User(email=email, hashed_password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
