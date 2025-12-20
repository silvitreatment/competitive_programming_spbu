import logging
from functools import wraps
from typing import Callable
import app.logging_handler
from flask import abort, current_app, g, redirect, request, session, url_for

from .models import User

logger = logging.getLogger(__name__)

ROLE_HIERARCHY = {"user": 0, "moderator": 1, "admin": 2}


def resolve_role(email: str | None = None, username: str | None = None) -> str:
    """Derive role from configured admin/moderator lists by email or telegram username."""
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
    logger.info(
        "Resolved role",
        extra={
            "role": role,
            "email": email or None,
            "username": username or None,
        },
    )
    return role


def set_current_user(user: User) -> None:
    session["user_id"] = user.id
    session["role"] = user.role
    session["logged_in"] = True
    logger.info("User session established", extra={"user_id": user.id, "role": user.role})


def require_login(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.current_user:
            logger.info("Redirected anonymous user to login", extra={"next": request.url})
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)

    return wrapped


def require_roles(*roles: str) -> Callable:
    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = g.current_user
            if not user or user.role not in roles:
                logger.warning(
                    "Access denied: insufficient role",
                    extra={"user_id": getattr(user, "id", None), "role": getattr(user, "role", None), "required": roles},
                )
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def load_current_user() -> None:
    user_id = session.get("user_id")
    g.current_user = User.query.get(user_id) if user_id else None
    logger.debug(
        "Loaded current user from session",
        extra={"user_id": user_id, "found": bool(g.current_user)},
    )


def inject_user() -> dict:
    return {
        "current_user": getattr(g, "current_user", None),
        "app_config": current_app.config,
    }


def register_auth(app) -> None:
    app.before_request(load_current_user)
    app.context_processor(inject_user)
    logger.info("Auth module registered")
