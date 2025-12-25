from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagCreate(TagBase):
    pass


class Tag(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    image_filename: Optional[str] = None
    tags: List[str] = []


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    image_filename: Optional[str] = None
    tags: Optional[List[str]] = []


class PostOut(PostBase):
    id: int
    author_id: int
    created_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class PostWithAuthor(PostOut):
    author: UserOut


class CommentBase(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(CommentBase):
    id: int
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommentWithAuthor(CommentOut):
    author: UserOut


class PostWithComments(PostWithAuthor):
    comments: List[CommentWithAuthor] = []


class ReactionBase(BaseModel):
    is_like: bool


class ReactionCreate(ReactionBase):
    pass


class ReactionOut(ReactionBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostReactions(BaseModel):
    likes_count: int = 0
    dislikes_count: int = 0
    user_reaction: Optional[bool] = None


class PostWithReactions(PostWithAuthor):
    reactions: PostReactions
