from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app import schemas, crud, auth
from app.config import settings

router = APIRouter(prefix="", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register(
        request: Request,
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: Session = Depends(get_db)
):
    errors = []

    if password != confirm_password:
        errors.append("Пароли не совпадают")

    if len(password) < 6:
        errors.append("Пароль должен быть не менее 6 символов")

    if crud.get_user_by_email(db, email):
        errors.append("Пользователь с таким email уже существует")

    if crud.get_user_by_username(db, username):
        errors.append("Пользователь с таким именем уже существует")

    if errors:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "email": email, "username": username}
        )

    user_create = schemas.UserCreate(
        email=email,
        username=username,
        password=password
    )
    crud.create_user(db, user_create)

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный email или пароль", "email": email}
        )

    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    next_url = request.query_params.get("next", "/")

    response = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800
    )
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response