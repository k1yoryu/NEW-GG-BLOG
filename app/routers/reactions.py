from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user, get_current_user_optional
from app import crud, schemas, models

router = APIRouter(tags=["reactions"])


@router.post("/posts/{post_id}/like")
async def like_post(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    reaction = schemas.ReactionCreate(is_like=True)
    crud.create_or_update_reaction(db, reaction, post_id, current_user.id)

    referer = request.headers.get("referer", f"/posts/{post_id}")
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/posts/{post_id}/dislike")
async def dislike_post(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):

    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    reaction = schemas.ReactionCreate(is_like=False)
    crud.create_or_update_reaction(db, reaction, post_id, current_user.id)

    referer = request.headers.get("referer", f"/posts/{post_id}")
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/posts/{post_id}/remove-reaction")
async def remove_reaction(
        post_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    crud.delete_reaction(db, post_id, current_user.id)

    referer = request.headers.get("referer", f"/posts/{post_id}")
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)