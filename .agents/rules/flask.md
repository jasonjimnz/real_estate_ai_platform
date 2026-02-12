## 1. Project Structure

We follow the **Application Factory Pattern**. Do not define your app in the global scope.

```text
project_root/
├── app/
│   ├── __init__.py          # Exports create_app()
│   ├── extensions.py        # Unbound extensions (db, migrate, etc.)
│   ├── models/              # Database entities (SQLAlchemy 2.0)
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base model
│   │   └── user.py
│   ├── api/                 # Routes (Blueprints)
│   │   ├── __init__.py
│   │   └── auth.py
│   └── services/            # Business Logic Layer
│       ├── __init__.py
│       └── user_service.py
├── migrations/              # Alembic migrations (Auto-generated)
├── tests/                   # Pytest suite
├── config.py                # Configuration Classes
├── .env                     # Secrets (GitIgnored)
├── requirements.txt
└── run.py                   # Application Entry Point

```

## 2. The Rules

### Rule #1: The Application Factory

All Flask applications must be created inside a factory function. This ensures thread safety and enables easy testing.

**File:** `app/__init__.py`

```python
from flask import Flask
from app.config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app

```

### Rule #2: Extension Isolation

Never import the `app` instance inside your extensions file. This prevents circular import errors.

**File:** `app/extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

```

### Rule #3: Modern Models (Python 3.12 + SQLA 2.0)

Use `Mapped[]` and `mapped_column()` for strict type hinting. Do not use legacy `db.Column`.

**File:** `app/models/user.py`

```python
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db
from app.models.base import BaseModel # Assumes a common base with timestamps

class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)

```

### Rule #4: The "Select" Syntax

Do not use `Model.query`. It is deprecated. Use `db.session.execute(select(...))`.

**File:** `app/services/user_service.py`

```python
from sqlalchemy import select
from app.extensions import db
from app.models.user import User

class UserService:
    @staticmethod
    def get_by_username(username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(username: str, email: str) -> User:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user

```

### Rule #5: Service Layer Separation

Routes must not contain business logic. Routes are for HTTP parsing only.

**File:** `app/api/auth.py`

```python
from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.post('/register')
def register():
    data = request.get_json()
    # Delegate logic to Service
    user = UserService.create(data['username'], data['email'])
    return jsonify({"id": user.id, "username": user.username}), 201

```

### Rule #6: Migration Discipline

Never use `db.create_all()`. Database schema changes must be versioned.

1. Modify the Python Model.
2. Run: `flask db migrate -m "Description of change"`
3. **Review the generated migration script.**
4. Run: `flask db upgrade`

## 3. Entry Point

Use a separated `run.py` to start the server. This decouples the app definition from the execution.

**File:** `run.py`

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

```

## 4. Configuration

Use a config class pattern that reads from environment variables.

**File:** `config.py`

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_fallback')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

```