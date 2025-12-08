from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from .extensions import db

_db_ready = False


def ensure_schema() -> None:
    inspector = inspect(db.engine)
    try:
        columns = {col["name"] for col in inspector.get_columns("article")}
    except OperationalError:
        db.create_all()
        columns = {col["name"] for col in inspector.get_columns("article")}

    with db.engine.begin() as conn:
        if "status" not in columns:
            conn.execute(text("ALTER TABLE article ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
        if "author_name" not in columns:
            conn.execute(text("ALTER TABLE article ADD COLUMN author_name VARCHAR(200)"))

        try:
            user_cols = {col["name"] for col in inspector.get_columns("user")}
        except OperationalError:
            db.create_all()
            user_cols = {col["name"] for col in inspector.get_columns("user")}

        if "password_hash" not in user_cols:
            conn.execute(text("ALTER TABLE user ADD COLUMN password_hash VARCHAR(255)"))


def initialize_database() -> None:
    global _db_ready
    if _db_ready:
        return
    db.create_all()
    ensure_schema()
    _db_ready = True


def register_db_hooks(app) -> None:
    @app.before_request
    def setup_db() -> None:
        initialize_database()
