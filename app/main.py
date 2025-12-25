from typing import Optional
from fastapi import FastAPI, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import app.models as models
from app.database import engine, get_db
from app.routers import auth, posts, comments, reactions, profile, simple_admin
from sqlalchemy.orm import Session
import time
from datetime import datetime, timedelta

app = FastAPI(title="GG-BLOG")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    max_retries = 5
    for i in range(max_retries):
        try:
            models.Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(3)


def moscow_time(dt: datetime) -> datetime:
    if dt:
        return dt + timedelta(hours=3)
    return dt

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
templates.env.filters["moscow_time"] = moscow_time
app.include_router(reactions.router)
app.include_router(profile.router)
app.include_router(simple_admin.router)

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None
    token = token[7:]
    from app.auth import verify_token
    username = verify_token(token)
    if not username:
        return None
    from app.crud import get_user_by_username
    return get_user_by_username(db, username)

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    try:
        total_posts = db.query(models.Post).count()
        skip = (page - 1) * per_page
        total_pages = (total_posts + per_page - 1) // per_page
        posts_list = db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(per_page).all()
        user_count = db.query(models.User).count()
    except:
        total_posts = 0
        total_pages = 1
        posts_list = []
        user_count = 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "post_count": total_posts,
            "user_count": user_count,
            "posts": posts_list,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page,
            "current_user": current_user
        }
    )


@app.get("/search", response_class=HTMLResponse)
async def search(
        request: Request,
        q: str = Query("", max_length=100),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    try:
        skip = (page - 1) * per_page

        posts_list = db.query(models.Post) \
            .filter(models.Post.title.ilike(f"%{q}%") |
                    models.Post.content.ilike(f"%{q}%")) \
            .order_by(models.Post.created_at.desc()) \
            .offset(skip) \
            .limit(per_page) \
            .all()

        total_results = db.query(models.Post) \
            .filter(models.Post.title.ilike(f"%{q}%") |
                    models.Post.content.ilike(f"%{q}%")) \
            .count()

        total_pages = (total_results + per_page - 1) // per_page
    except:
        posts_list = []
        total_results = 0
        total_pages = 1

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "posts": posts_list,
            "query": q,
            "total_results": total_results,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page,
            "current_user": current_user
        }
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/tag/{tag_name}", response_class=HTMLResponse)
async def posts_by_tag(
        tag_name: str,
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    try:
        skip = (page - 1) * per_page

        posts_list = db.query(models.Post) \
            .join(models.Post.tags) \
            .filter(models.Tag.name == tag_name) \
            .order_by(models.Post.created_at.desc()) \
            .offset(skip) \
            .limit(per_page) \
            .all()

        total_posts = db.query(models.Post) \
            .join(models.Post.tags) \
            .filter(models.Tag.name == tag_name) \
            .count()

        total_pages = (total_posts + per_page - 1) // per_page
    except:
        posts_list = []
        total_posts = 0
        total_pages = 1

    return templates.TemplateResponse(
        "tag.html",
        {
            "request": request,
            "tag_name": tag_name,
            "posts": posts_list,
            "total_posts": total_posts,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page,
            "current_user": current_user
        }
    )
