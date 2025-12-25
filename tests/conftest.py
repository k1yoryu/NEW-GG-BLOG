import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from app.config import settings
import os

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


@pytest.fixture(scope="function")
def test_user(db_session):
    from app.models import User
    from app.auth import get_password_hash

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def test_post(db_session, test_user):
    from app.models import Post

    post = Post(
        title="Test Post Title",
        content="Test post content for testing purposes.",
        author_id=test_user.id
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    return post


@pytest.fixture(scope="function")
def auth_client(test_client, test_user):
    # Логинимся чтобы получить токен
    response = test_client.post("/login", data={
        "email": test_user.email,
        "password": "testpassword123"
    })

    return test_client


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests as authentication related"
    )
    config.addinivalue_line(
        "markers", "db: marks tests that require database"
    )