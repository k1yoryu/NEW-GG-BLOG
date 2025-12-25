from typing import Optional
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form, File, UploadFile
from app.config import settings
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.dependencies import get_db, get_current_user, get_current_user_optional

router = APIRouter(prefix="", tags=["posts"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/posts/", response_model=list[schemas.PostWithAuthor])
def read_posts_api(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts


@router.post("/posts/", response_model=schemas.PostOut)
def create_post_api(
        post: schemas.PostCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return crud.create_post(db=db, post=post, author_id=current_user.id)


@router.get("/posts/{post_id}/api", response_model=schemas.PostWithAuthor)
def read_post_api(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post_api(
        post_id: int,
        post_update: schemas.PostUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_post = crud.update_post(db, post_id, post_update, current_user.id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return db_post


@router.delete("/posts/{post_id}")
def delete_post_api(
        post_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    success = crud.delete_post(db, post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return {"message": "Post deleted successfully"}


@router.get("/posts/create", response_class=HTMLResponse)
async def create_post_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    if not current_user:
        response = RedirectResponse(url=f"/login?next=/posts/create", status_code=status.HTTP_302_FOUND)
        return response

    return templates.TemplateResponse("create_post.html", {"request": request})


@router.post("/posts/create", response_class=HTMLResponse)
async def create_post(
        request: Request,
        title: str = Form(...),
        content: str = Form(...),
        tags: str = Form(""),
        image: UploadFile = File(None),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):

    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    image_filename = None

    if image and image.filename:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        import uuid
        file_ext = os.path.splitext(image.filename)[1]
        image_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, image_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    post_create = schemas.PostCreate(
        title=title,
        content=content,
        tags=tag_list,
        image_filename=image_filename
    )
    crud.create_post(db, post_create, current_user.id, image_filename)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    comments = crud.get_comments_by_post(db, post_id)
    reactions = crud.get_post_reactions(db, post_id)
    user_reaction = crud.get_user_reaction(db, post_id, current_user.id) if current_user else None

    return templates.TemplateResponse("post_detail.html", {
        "request": request,
        "post": post,
        "comments": comments,
        "reactions": reactions,
        "user_reaction": user_reaction,
        "current_user": current_user
    })


@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_page(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    post = crud.get_post(db, post_id)
    if not post or post.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Пост не найден или недостаточно прав")

    return templates.TemplateResponse("edit_post.html", {
        "request": request,
        "post": post
    })


@router.post("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post(
        post_id: int,
        request: Request,
        title: str = Form(...),
        content: str = Form(...),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    post_update = schemas.PostUpdate(title=title, content=content)
    db_post = crud.update_post(db, post_id, post_update, current_user.id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден или недостаточно прав")

    return RedirectResponse(url=f"/posts/{post_id}", status_code=status.HTTP_302_FOUND)


@router.post("/posts/{post_id}/delete", response_class=HTMLResponse)
async def delete_post_handler(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    success = crud.delete_post(db, post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Пост не найден или недостаточно прав")

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)