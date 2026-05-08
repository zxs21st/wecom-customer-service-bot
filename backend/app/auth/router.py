import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.db import get_db
from app.models.admin import AdminUser
from app.auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    """管理员登录"""
    from sqlalchemy import select
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}
