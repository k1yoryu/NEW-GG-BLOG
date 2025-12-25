from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.crud import get_user_by_username
from app.models import User


def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )

    token = token[7:]
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )

    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )

    return user


def get_current_user_optional(
        request: Request,
        db: Session = Depends(get_db)
) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None

    token = token[7:]
    username = verify_token(token)
    if not username:
        return None

    return get_user_by_username(db, username)