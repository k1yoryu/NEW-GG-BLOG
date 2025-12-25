# tests/test_posts.py
import pytest
from fastapi import status


@pytest.mark.db
class TestPosts:


    def test_get_posts_list(self, test_client):

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert "Последние посты" in response.text

    def test_create_post_unauthorized(self, test_client):

        response = test_client.get("/posts/create")


        assert response.status_code in [302, 303]
        assert "/login" in str(response.url)

    def test_create_post_authorized(self, auth_client, test_user):

        response = auth_client.get("/posts/create")
        assert response.status_code == status.HTTP_200_OK
        assert "Создать пост" in response.text


        response = auth_client.post("/posts/create", data={
            "title": "Test Post Title",
            "content": "Test post content for testing.",
            "tags": "python, testing",
            "image": ""
        })

        assert response.status_code in [200, 302, 303]

    def test_view_post(self, test_client, test_post):
        response = test_client.get(f"/posts/{test_post.id}")

        assert response.status_code == status.HTTP_200_OK
        assert test_post.title in response.text
        assert test_post.content in response.text

    def test_view_nonexistent_post(self, test_client):
        response = test_client.get("/posts/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_edit_post_owner(self, auth_client, test_user, test_post):
        response = auth_client.get(f"/posts/{test_post.id}/edit")

        assert response.status_code == status.HTTP_200_OK
        assert "Редактировать пост" in response.text
        assert test_post.title in response.text

    def test_edit_post_not_owner(self, test_client, db_session, test_post):
        from app.models import User
        from app.auth import get_password_hash

        other_user = User(
            email="other@test.com",
            username="otheruser",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        client = test_client
        client.post("/login", data={
            "email": "other@test.com",
            "password": "password123"
        })

        response = client.get(f"/posts/{test_post.id}/edit")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.slow
    def test_delete_post(self, auth_client, test_user, db_session):
        from app.models import Post
        post_to_delete = Post(
            title="Post to delete",
            content="Content",
            author_id=test_user.id
        )
        db_session.add(post_to_delete)
        db_session.commit()

        response = auth_client.post(f"/posts/{post_to_delete.id}/delete")

        assert response.status_code in [302, 303]

        deleted_post = db_session.query(Post).filter_by(id=post_to_delete.id).first()
        assert deleted_post is None

    def test_search_posts(self, test_client, test_post):
        response = test_client.get(f"/search?q={test_post.title}")

        assert response.status_code == status.HTTP_200_OK
        assert test_post.title in response.text

    def test_posts_by_tag(self, test_client, db_session, test_user):
        from app.models import Post, Tag

        tag = Tag(name="pytest")
        post = Post(
            title="Post with pytest tag",
            content="Content",
            author_id=test_user.id
        )
        post.tags.append(tag)

        db_session.add_all([tag, post])
        db_session.commit()

        response = test_client.get(f"/tag/{tag.name}")

        assert response.status_code == status.HTTP_200_OK
        assert post.title in response.text