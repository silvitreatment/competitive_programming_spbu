from functools import wraps
from typing import Callableandler
from flask import abort, current_app, g, redirect, request, session, url_for

from .models import User


ROLE_HIERARCHY = {"user": 0, "moderator": 1, "admin": 2}


def resolve_role(email: str | None = None, username: str | None = None) -> str:
    email = (email or "").lower()
    username = (username or "").lstrip("@").lower()
    admin_emails = current_app.config.get("ADMIN_EMAILS", [])
    moderator_emails = current_app.config.get("MODERATOR_EMAILS", [])
    admin_telegrams = current_app.config.get("ADMIN_TELEGRAMS", [])
    moderator_telegrams = current_app.config.get("MODERATOR_TELEGRAMS", [])

    role = "user"
    if email and email in admin_emails:
        role = "admin"
    if email and email in moderator_emails:
        role = "moderator"
    if username and username in admin_telegrams:
        role = "admin"
    if username and username in moderator_telegrams:
        role = "moderator"
    return role


def set_current_user(user: User) -> None:
    session["user_id"] = user.id
    session["role"] = user.role


def require_login(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.current_user:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped


def require_roles(*roles: str) -> Callable:
    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = g.current_user
            if not user or user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped
    return decorator


def load_current_user() -> None:
    user_id = session.get("user_id")
    g.current_user = User.query.get(user_id) if user_id else None


def inject_user() -> dict:
    return {
        "current_user": getattr(g, "current_user", None),
        "app_config": current_app.config,
    }


def register_auth(app) -> None:
    app.before_request(load_current_user)
    app.context_processor(inject_user)
