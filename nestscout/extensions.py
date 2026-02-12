"""Unbound Flask extensions — initialised in create_app().

Never import the app instance here. These are bound to the app
via ext.init_app(app) inside the factory function.
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
cors = CORS()
