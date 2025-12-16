from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from .auth import register_auth
from .config import Config
from .db_utils import initialize_database, register_db_hooks
from .extensions import db
from .routes import register_routes


def create_app(config_class: type = Config) -> Flask:
    """Application factory that wires extensions, auth, routes and DB checks."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    register_db_hooks(app)
    register_auth(app)
    register_routes(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Make sure schema exists before serving requests (mirrors lazy hook).
    with app.app_context():
        initialize_database()

    return app
