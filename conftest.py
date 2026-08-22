import pytest
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from api import app
from db import get_session




test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture(name="session")
def session_fixture():

    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session

    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()