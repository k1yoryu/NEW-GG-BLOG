from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app import crud, schemas, models

router = APIRouter(tags=["comments"])


@router.post("/posts/{post_id}/comments/")
async def create_comment(
        post_id: int,
        request: Request,
        content: str = Form(...),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    comment_create = schemas.CommentCreate(content=content)
    crud.create_comment(db, comment_create, current_user.id, post_id)

    return RedirectResponse(url=f"/posts/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/posts/{post_id}/comments/{comment_id}/delete")
async def delete_comment(
        post_id: int,
        comment_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    comment = crud.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    crud.delete_comment(db, comment_id, current_user.id)

    return RedirectResponse(url=f"/posts/{post_id}", status_code=status.HTTP_303_SEE_OTHER)