
 import pytest
from fastapi import status


@pytest.mark.auth
class TestAuthentication:


    def test_register_user(self, test_client, db_session):

        response = test_client.post("/register", data={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "newpass123",
            "confirm_password": "newpass123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "Регистрация успешна" in response.text


        from app.models import User
        user = db_session.query(User).filter_by(email="newuser@test.com").first()
        assert user is not None
        assert user.username == "newuser"

    def test_register_duplicate_email(self, test_client, test_user):

        response = test_client.post("/register", data={
            "email": test_user.email,
            "username": "differentuser",
            "password": "password123",
            "confirm_password": "password123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "уже зарегистрирован" in response.text.lower()

    def test_login_success(self, test_client, test_user):

        response = test_client.post("/login", data={
            "email": test_user.email,
            "password": "testpassword123"
        })

        assert response.status_code == status.HTTP_200_OK

        assert response.url.path == "/"


        assert "access_token" in response.cookies

    def test_login_wrong_password(self, test_client, test_user):

        response = test_client.post("/login", data={
            "email": test_user.email,
            "password": "wrongpassword"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "неверный email или пароль" in response.text.lower()

    def test_login_nonexistent_user(self, test_client):

        response = test_client.post("/login", data={
            "email": "nonexistent@test.com",
            "password": "password123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "неверный email или пароль" in response.text.lower()

    def test_logout(self, auth_client):

        response = auth_client.get("/logout")

        assert response.status_code == status.HTTP_200_OK

        assert response.url.path == "/"

    @pytest.mark.integration
    def test_protected_route_no_auth(self, test_client):

        response = test_client.get("/profile")


        assert response.status_code in [302, 303]
        assert "/login" in str(response.url)

    def test_protected_route_with_auth(self, auth_client, test_user):

        response = auth_client.get(f"/profile/{test_user.username}")

        assert response.status_code == status.HTTP_200_OK
        assert test_user.username in response.text