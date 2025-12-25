from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import User, Post, Comment

router = APIRouter()

ADMINS = [
    "test@gmail.com",
    "saksaksak",
]


def check_admin(user: User) -> bool:
    return user.email in ADMINS or user.username in ADMINS


@router.get("/admin")
async def admin_page(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    if not check_admin(current_user):
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <body style="padding: 20px; font-family: Arial;">
            <h1 style="color: red;"> Доступ запрещен!</h1>
            <p>У вас нет прав администратора.</p>
            <a href="/">На главную</a>
        </body>
        </html>
        """, status_code=403)

    total_posts = db.query(Post).count()
    total_users = db.query(User).count()
    total_comments = db.query(Comment).count()

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Админка GG Blog</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 20px; }}
            .admin-badge {{ background: gold; padding: 3px 8px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👑 АДМИНКА GG Blog</h1>
            <p>Привет, <span class="admin-badge">{current_user.username}</span>!</p>

            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <h5>👥 Пользователи</h5>
                            <h2>{total_users}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <h5>📝 Посты</h5>
                            <h2>{total_posts}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <h5>💬 Комментарии</h5>
                            <h2>{total_comments}</h2>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-4">
                <h3>Действия:</h3>
                <div class="btn-group">
                    <a href="/" class="btn btn-outline-primary">На главную</a>
                    <a href="/admin/users" class="btn btn-outline-success">Список пользователей</a>
                    <a href="/admin/posts" class="btn btn-outline-warning">Список постов</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)


@router.get("/admin/users")
async def admin_users(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not check_admin(current_user):
        return HTMLResponse("Нет прав!", status_code=403)

    users = db.query(User).order_by(User.created_at.desc()).all()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Пользователи</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>👥 Все пользователи</h1>
        <a href="/admin" class="btn btn-secondary mb-3">← Назад в админку</a>

        <table class="table">
            <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Email</th>
                <th>Зарегистрирован</th>
            </tr>
    """

    for user in users:
        is_admin = "👑" if check_admin(user) else ""
        html += f"""
            <tr>
                <td>{user.id}</td>
                <td>{is_admin} <a href="/profile/{user.username}">{user.username}</a></td>
                <td>{user.email}</td>
                <td>{user.created_at.strftime('%d.%m.%Y')}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return HTMLResponse(html)


@router.get("/admin/posts")
async def admin_posts(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not check_admin(current_user):
        return HTMLResponse("Нет прав!", status_code=403)

    posts = db.query(Post).order_by(Post.created_at.desc()).limit(50).all()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Посты</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>📝 Все посты</h1>
        <a href="/admin" class="btn btn-secondary mb-3">← Назад в админку</a>
    """

    for post in posts:
        html += f"""
        <div class="card mb-3">
            <div class="card-body">
                <h5>{post.title}</h5>
                <p>Автор: <a href="/profile/{post.author.username}">{post.author.username}</a></p>
                <p>Дата: {post.created_at.strftime('%d.%m.%Y %H:%M')}</p>
                <div>
                    <a href="/posts/{post.id}" class="btn btn-sm btn-primary">Открыть</a>
                    <a href="/posts/{post.id}" class="btn btn-sm btn-outline-secondary">Комментарии ({len(post.comments)})</a>
                </div>
            </div>
        </div>
        """

    html += "</body></html>"
    return HTMLResponse(html)