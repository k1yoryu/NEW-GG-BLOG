from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.dependencies import get_db, get_current_user, get_current_user_optional
from app import crud, models, auth
from app.auth import verify_password, get_password_hash

router = APIRouter(prefix="", tags=["profile"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile/{username}", response_class=HTMLResponse)
async def user_profile(
        username: str,
        request: Request,
        tab: str = "posts",  # posts, liked, comments
        page: int = 1,
        per_page: int = 10,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user_optional)
):

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    stats = get_user_stats(db, user.id)


    data = []
    total_items = 0

    if tab == "posts":
        skip = (page - 1) * per_page
        data = get_user_posts(db, user.id, skip, per_page)
        total_items = stats["posts_count"]
    elif tab == "liked":
        skip = (page - 1) * per_page
        data = get_user_liked_posts(db, user.id, skip, per_page)
        total_items = stats["likes_given"]
    elif tab == "comments":
        skip = (page - 1) * per_page
        data = get_user_comments(db, user.id, skip, per_page)
        total_items = stats["comments_count"]

    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1

    is_owner = current_user and current_user.id == user.id

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile_user": user,
        "current_user": current_user,
        "is_owner": is_owner,
        "tab": tab,
        "data": data,
        "stats": stats,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


@router.get("/profile", response_class=HTMLResponse)
async def my_profile(
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return RedirectResponse(url=f"/profile/{current_user.username}", status_code=302)


@router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(
        request: Request,
        current_user: models.User = Depends(get_current_user)
):
    return templates.TemplateResponse("change_password.html", {
        "request": request,
        "current_user": current_user
    })


@router.post("/change-password", response_class=HTMLResponse)
async def change_password(
        request: Request,
        current_password: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not verify_password(current_password, current_user.hashed_password):
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "current_user": current_user,
            "error": "Неверный текущий пароль"
        })

    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "current_user": current_user,
            "error": "Новые пароли не совпадают"
        })

    current_user.hashed_password = get_password_hash(new_password)
    db.commit()

    return RedirectResponse(url=f"/profile/{current_user.username}?message=Пароль успешно изменен", status_code=302)


def get_user_posts(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return (db.query(models.Post)
            .filter(models.Post.author_id == user_id)
            .order_by(models.Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all())


def get_user_liked_posts(db: Session, user_id: int, skip: int = 0, limit: int = 10):

    return (db.query(models.Post)
            .join(models.Reaction)
            .filter(
        models.Reaction.user_id == user_id,
        models.Reaction.is_like == True
    )
            .order_by(models.Reaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all())


def get_user_comments(db: Session, user_id: int, skip: int = 0, limit: int = 10):

    return (db.query(models.Comment)
            .filter(models.Comment.author_id == user_id)
            .order_by(models.Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all())


def get_user_stats(db: Session, user_id: int):
    posts_count = db.query(models.Post).filter(models.Post.author_id == user_id).count()
    comments_count = db.query(models.Comment).filter(models.Comment.author_id == user_id).count()
    likes_given = db.query(models.Reaction).filter(
        models.Reaction.user_id == user_id,
        models.Reaction.is_like == True
    ).count()
    dislikes_given = db.query(models.Reaction).filter(
        models.Reaction.user_id == user_id,
        models.Reaction.is_like == False
    ).count()

    return {
        "posts_count": posts_count,
        "comments_count": comments_count,
        "likes_given": likes_given,
        "dislikes_given": dislikes_given,
    }