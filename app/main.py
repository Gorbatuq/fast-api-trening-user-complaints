from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from jose import JWTError, jwt
from datetime import timedelta

from . import models, auth, crud
from .database import Base

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session


@app.post("/register")
async def register_user(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, form.username)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await crud.create_user(db, form.username, form.password)
    return {"email": new_user.email}


@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, form.username)
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="Invalid token")
    try:
        payload = jwt.decode(token, auth.SECRET_KEY,
                             algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


@app.post("/complaints")
async def create_complaint(text: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    complaint = models.Complaint(text=text, owner_id=user.id)
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return {"id": complaint.id, "text": complaint.text}


@app.get("/complaints")
async def list_complaints(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Complaint).where(models.Complaint.owner_id == user.id)
    )
    return result.scalars().all()
