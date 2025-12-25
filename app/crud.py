from sqlalchemy.orm import Session
from sqlalchemy import Integer
from typing import Optional
from sqlalchemy import func
from app import models, schemas
from app.auth import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_or_create_tag(db: Session, tag_name: str):
    tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
    if not tag:
        tag = models.Tag(name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag


def create_post(db: Session, post: schemas.PostCreate, user_id: int, image_filename: str = None):
    db_post = models.Post(
        title=post.title,
        content=post.content,
        author_id=user_id,
        image_filename=image_filename
    )

    if hasattr(post, 'tags') and post.tags:
        for tag_name in post.tags:
            tag = get_or_create_tag(db, tag_name.strip())
            db_post.tags.append(tag)

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Post).offset(skip).limit(limit).all()


def update_post(db: Session, post_id: int, post_update: schemas.PostUpdate, user_id: int):
    db_post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.author_id == user_id
    ).first()

    if db_post:
        update_data = post_update.dict(exclude_unset=True, exclude={'tags'})
        for field, value in update_data.items():
            setattr(db_post, field, value)

        if 'tags' in post_update.dict(exclude_unset=True):
            db_post.tags.clear()
            for tag_name in post_update.tags:
                tag = get_or_create_tag(db, tag_name.strip())
                db_post.tags.append(tag)

        db.commit()
        db.refresh(db_post)

    return db_post


def delete_post(db: Session, post_id: int, user_id: int):
    db_post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.author_id == user_id
    ).first()

    if db_post:

        db.query(models.Reaction).filter(
            models.Reaction.post_id == post_id
        ).delete()

        db.query(models.Comment).filter(
            models.Comment.post_id == post_id
        ).delete()

        db.delete(db_post)
        db.commit()
        return True

    return False


def search_posts(db: Session, search_query: str, skip: int = 0, limit: int = 10):
    return db.query(models.Post) \
        .filter(models.Post.title.ilike(f"%{search_query}%") |
                models.Post.content.ilike(f"%{search_query}%")) \
        .order_by(models.Post.created_at.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all()


def count_search_posts(db: Session, search_query: str):
    return db.query(models.Post) \
        .filter(models.Post.title.ilike(f"%{search_query}%") |
                models.Post.content.ilike(f"%{search_query}%")) \
        .count()


def get_posts_by_tag(db: Session, tag_name: str, skip: int = 0, limit: int = 10):
    return db.query(models.Post) \
        .join(models.Post.tags) \
        .filter(models.Tag.name == tag_name) \
        .order_by(models.Post.created_at.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all()


def get_all_tags(db: Session):
    return db.query(models.Tag).order_by(models.Tag.name).all()


def get_popular_tags(db: Session, limit: int = 10):
    return db.query(models.Tag, func.count(models.post_tags.c.post_id).label('count')) \
        .join(models.post_tags) \
        .group_by(models.Tag.id) \
        .order_by(func.count(models.post_tags.c.post_id).desc()) \
        .limit(limit) \
        .all()


def create_comment(db: Session, comment: schemas.CommentCreate, author_id: int, post_id: int):
    db_comment = models.Comment(
        content=comment.content,
        author_id=author_id,
        post_id=post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment(db: Session, comment_id: int):
    return db.query(models.Comment).filter(models.Comment.id == comment_id).first()


def get_comments_by_post(db: Session, post_id: int, skip: int = 0, limit: int = 100):
    return (db.query(models.Comment)
            .filter(models.Comment.post_id == post_id)
            .order_by(models.Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all())


def update_comment(db: Session, comment_id: int, comment_update: schemas.CommentUpdate, author_id: int):
    db_comment = db.query(models.Comment).filter(
        models.Comment.id == comment_id,
        models.Comment.author_id == author_id
    ).first()

    if db_comment:
        for field, value in comment_update.dict(exclude_unset=True).items():
            setattr(db_comment, field, value)
        db.commit()
        db.refresh(db_comment)

    return db_comment


def delete_comment(db: Session, comment_id: int, author_id: int):
    db_comment = db.query(models.Comment).filter(
        models.Comment.id == comment_id,
        models.Comment.author_id == author_id
    ).first()

    if db_comment:
        db.delete(db_comment)
        db.commit()
        return True

    return False


def get_comments_count_by_post(db: Session, post_id: int):
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).count()

def create_or_update_reaction(db: Session, reaction: schemas.ReactionCreate, post_id: int, user_id: int):
    db_reaction = db.query(models.Reaction).filter(
        models.Reaction.post_id == post_id,
        models.Reaction.user_id == user_id
    ).first()

    if db_reaction:
        if db_reaction.is_like == reaction.is_like:
            db.delete(db_reaction)
            db.commit()
            return None
        else:
            db_reaction.is_like = reaction.is_like
            db_reaction.created_at = func.now()
    else:
        db_reaction = models.Reaction(
            post_id=post_id,
            user_id=user_id,
            is_like=reaction.is_like
        )
        db.add(db_reaction)

    db.commit()
    db.refresh(db_reaction)
    return db_reaction


def get_post_reactions(db: Session, post_id: int):
    from sqlalchemy import func

    result = db.query(
        func.sum(models.Reaction.is_like.cast(Integer)).label('likes'),
        func.sum((~models.Reaction.is_like).cast(Integer)).label('dislikes')
    ).filter(models.Reaction.post_id == post_id).first()

    return {
        'likes_count': result.likes or 0,
        'dislikes_count': result.dislikes or 0
    }


def get_user_reaction(db: Session, post_id: int, user_id: int):
    reaction = db.query(models.Reaction).filter(
        models.Reaction.post_id == post_id,
        models.Reaction.user_id == user_id
    ).first()

    return reaction.is_like if reaction else None


def get_post_with_reactions(db: Session, post_id: int, user_id: Optional[int] = None):
    post = get_post(db, post_id)
    if not post:
        return None

    reactions = get_post_reactions(db, post_id)
    user_reaction = get_user_reaction(db, post_id, user_id) if user_id else None

    return {
        'post': post,
        'reactions': reactions,
        'user_reaction': user_reaction
    }


def delete_reaction(db: Session, post_id: int, user_id: int):
    reaction = db.query(models.Reaction).filter(
        models.Reaction.post_id == post_id,
        models.Reaction.user_id == user_id
    ).first()

    if reaction:
        db.delete(reaction)
        db.commit()
        return True

    return False