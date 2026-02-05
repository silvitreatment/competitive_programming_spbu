from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from flask import current_app

_db_ready = False


def _alembic_config() -> AlembicConfig:
    project_root = Path(__file__).resolve().parents[1]
    alembic_ini = project_root / "alembic.ini"
    config = AlembicConfig(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", current_app.config["SQLALCHEMY_DATABASE_URI"])
    return config


def initialize_database() -> None:
    global _db_ready
    if _db_ready:
        return
    config = _alembic_config()
    command.upgrade(config, "head")
    _db_ready = True


def register_db_hooks(app) -> None:
    @app.before_request
    def setup_db() -> None:
        initialize_database()
