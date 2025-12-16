import os
from typing import List


def _split_env_list(env_value: str) -> List[str]:
    return [entry.strip().lower() for entry in env_value.split(",") if entry.strip()]


def _env_flag(value: str | None) -> bool:
    return bool(value and value.strip().lower() in ("1", "true", "yes", "on"))


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///knowledge.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("SECRET_KEY", "SOME_SECRET_KEY")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")
    GOOGLE_CLIENT_ID = os.environ.get(
        "GOOGLE_CLIENT_ID",
        "42776546874-ni1bv31g5f4ce8t361456tf685pmm4f0.apps.googleusercontent.com",
    )
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    YANDEX_CLIENT_ID = os.environ.get("YANDEX_CLIENT_ID")
    YANDEX_CLIENT_SECRET = os.environ.get("YANDEX_CLIENT_SECRET")
    # Яндекс ожидает пробел-разделитель; состав прав — email, профиль, аватар, дата рождения, телефон.
    YANDEX_SCOPE_DEFAULT = "login:email login:info login:avatar login:birthday login:phone"
    YANDEX_SCOPE = os.environ.get("YANDEX_SCOPE") or YANDEX_SCOPE_DEFAULT

    ADMIN_EMAILS = _split_env_list(os.environ.get("ADMIN_EMAILS", ""))
    MODERATOR_EMAILS = _split_env_list(os.environ.get("MODERATOR_EMAILS", ""))
    ADMIN_TELEGRAMS = _split_env_list(os.environ.get("ADMIN_TELEGRAMS", ""))
    MODERATOR_TELEGRAMS = _split_env_list(os.environ.get("MODERATOR_TELEGRAMS", ""))

    # HTTPS settings: provide cert/key paths or set SSL_ADHOC=1 for a self-signed dev cert.
    SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH")
    SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH")
    SSL_ADHOC = _env_flag(os.environ.get("SSL_ADHOC"))
