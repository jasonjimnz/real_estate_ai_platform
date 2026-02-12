"""Test fixtures and configuration."""

import pytest

from nestscout import create_app
from nestscout.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create the Flask test app."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Per-test database session with rollback."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
