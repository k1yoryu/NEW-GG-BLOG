import pytest
from fastapi import status


@pytest.mark.db
class TestComments:

    def test_add_comment_unauthorized(self, test_client, test_post):
        response = test_client.post(
            f"/posts/{test_post.id}/comments/",
            data={"content": "Test comment"}
        )

        assert response.status_code in [302, 303]
        assert "/login" in str(response.url)

    def test_add_comment_authorized(self, auth_client, test_post):
        response = auth_client.post(
            f"/posts/{test_post.id}/comments/",
            data={"content": "Test comment from authorized user"}
        )

        assert response.status_code in [302, 303]

    def test_view_post_with_comments(self, test_client, db_session, test_user, test_post):
        from app.models import Comment

        comment1 = Comment(
            content="First comment",
            author_id=test_user.id,
            post_id=test_post.id
        )
        comment2 = Comment(
            content="Second comment",
            author_id=test_user.id,
            post_id=test_post.id
        )
        db_session.add_all([comment1, comment2])
        db_session.commit()

        response = test_client.get(f"/posts/{test_post.id}")

        assert response.status_code == status.HTTP_200_OK
        assert "First comment" in response.text
        assert "Second comment" in response.text
        assert "Комментарии (2)" in response.text

    def test_delete_comment_owner(self, auth_client, test_user, db_session):
        from app.models import Post, Comment

        post = Post(
            title="Post for comment deletion",
            content="Content",
            author_id=test_user.id
        )
        comment = Comment(
            content="Comment to delete",
            author_id=test_user.id,
            post_id=post.id
        )
        db_session.add_all([post, comment])
        db_session.commit()

        response = auth_client.post(
            f"/posts/{post.id}/comments/{comment.id}/delete"
        )

        assert response.status_code in [302, 303]

        deleted_comment = db_session.query(Comment).filter_by(id=comment.id).first()
        assert deleted_comment is None

    @pytest.mark.integration
    def test_comment_lifecycle(self, auth_client, db_session, test_user):
        """Полный жизненный цикл комментария"""
        from app.models import Post, Comment

        post = Post(
            title="Integration test post",
            content="Content",
            author_id=test_user.id
        )
        db_session.add(post)
        db_session.commit()

        response = auth_client.post(
            f"/posts/{post.id}/comments/",
            data={"content": "Integration test comment"}
        )
        assert response.status_code in [302, 303]

        response = auth_client.get(f"/posts/{post.id}")
        assert "Integration test comment" in response.text

        comment = db_session.query(Comment).filter_by(
            post_id=post.id,
            author_id=test_user.id
        ).first()

        response = auth_client.post(
            f"/posts/{post.id}/comments/{comment.id}/delete"
        )
        assert response.status_code in [302, 303]

        response = auth_client.get(f"/posts/{post.id}")
        assert "Integration test comment" not in response.text