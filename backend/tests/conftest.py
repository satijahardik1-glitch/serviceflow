import os
import shutil
import tempfile

_tmp = tempfile.mkdtemp()
DB_PATH = os.path.join(_tmp, "test.db")
TEMPLATE_PATH = os.path.join(_tmp, "template.db")
USE_PG = bool(os.environ.get("TEST_DATABASE_URL"))  # run the suite against a real PostgreSQL
os.environ.update(
    ENVIRONMENT="test", DATABASE_URL=os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{DB_PATH}", RATE_LIMIT_ENABLED="true",
    SECRET_KEY="test-secret-key-test-secret-key-1234567890", ENCRYPTION_KEY="",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
import seed  # noqa: E402
from app.core.ratelimit import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _template_db():
    """Seed once (bcrypt is slow), then copy the seeded file for every test."""
    if USE_PG:
        return
    Base.metadata.create_all(engine)
    seed.main(reset=False)
    engine.dispose()
    shutil.copyfile(DB_PATH, TEMPLATE_PATH)


@pytest.fixture(autouse=True)
def fresh_db(_template_db):
    if USE_PG:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        seed.main(reset=False)
    else:
        engine.dispose()
        shutil.copyfile(TEMPLATE_PATH, DB_PATH)
    limiter.reset()
    yield
    engine.dispose()


@pytest.fixture
def client():
    return TestClient(app)


PASSWORDS = {"admin": "Admin@123", "neha": "Customer@123", "arjun": "Customer@123"}


@pytest.fixture
def login(client):
    def _login(email, password=None):
        password = password or ("Admin@123" if email.startswith("admin") else "Customer@123" if email.endswith("example.com") else "Tech@1234")
        r = client.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _login


@pytest.fixture
def customer(login):
    return login("neha@example.com")


@pytest.fixture
def customer2(login):
    return login("arjun@example.com")


@pytest.fixture
def admin(login):
    return login("admin@serviceflow.com")


@pytest.fixture
def rajesh(login):
    return login("rajesh@serviceflow.com")
