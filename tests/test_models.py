import pytest
from datetime import datetime
from app.models import User, Post, Comment, Reaction, Tag


@pytest.mark.db
class TestModels:


    def test_create_user(self, db_session):

        user = User(
            email="user@test.com",
            username="usertest",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "user@test.com"
        assert user.username == "usertest"
        assert user.is_active == True
        assert isinstance(user.created_at, datetime)

    def test_user_relationships(self, db_session, test_user, test_post):
        assert hasattr(test_user, 'posts')
        assert isinstance(test_user.posts, list)

        assert test_post.author_id == test_user.id
        assert test_post.author == test_user

    def test_create_post(self, db_session, test_user):

        post = Post(
            title="Test Post",
            content="Test content",
            author_id=test_user.id
        )
        db_session.add(post)
        db_session.commit()

        assert post.id is not None
        assert post.title == "Test Post"
        assert post.author == test_user
        assert isinstance(post.created_at, datetime)

    @pytest.mark.slow
    def test_post_with_tags(self, db_session, test_user):

        from app.models import Tag


        tag1 = Tag(name="python")
        tag2 = Tag(name="fastapi")
        db_session.add_all([tag1, tag2])
        db_session.commit()


        post = Post(
            title="Post with Tags",
            content="Content",
            author_id=test_user.id
        )
        post.tags.append(tag1)
        post.tags.append(tag2)

        db_session.add(post)
        db_session.commit()

        assert len(post.tags) == 2
        assert "python" in [tag.name for tag in post.tags]
        assert "fastapi" in [tag.name for tag in post.tags]

    def test_create_comment(self, db_session, test_user, test_post):

        comment = Comment(
            content="Test comment",
            author_id=test_user.id,
            post_id=test_post.id
        )
        db_session.add(comment)
        db_session.commit()

        assert comment.id is not None
        assert comment.content == "Test comment"
        assert comment.author == test_user
        assert comment.post == test_post

    def test_create_reaction(self, db_session, test_user, test_post):

        reaction = Reaction(
            post_id=test_post.id,
            user_id=test_user.id,
            is_like=True
        )
        db_session.add(reaction)
        db_session.commit()

        assert reaction.id is not None
        assert reaction.is_like == True
        assert reaction.post == test_post
        assert reaction.user == test_user

    @pytest.mark.integration
    def test_cascade_delete(self, db_session, test_user):


        post = Post(
            title="Cascade Test",
            content="Content",
            author_id=test_user.id
        )
        db_session.add(post)
        db_session.commit()


        comment = Comment(
            content="Comment to delete",
            author_id=test_user.id,
            post_id=post.id
        )
        db_session.add(comment)
        db_session.commit()


        db_session.delete(post)
        db_session.commit()


        remaining_comments = db_session.query(Comment).filter_by(post_id=post.id).all()
        assert len(remaining_comments) == 0