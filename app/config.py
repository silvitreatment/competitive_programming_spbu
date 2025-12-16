import os
from typing import List


def _split_env_list(env_value: str) -> List[str]:
    return [entry.strip().lower() for entry in env_value.split(',') if entry.strip()]


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///knowledge.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get('SECRET_KEY', 'SOME_SECRET_KEY')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password123')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    ADMIN_EMAILS = _split_env_list(os.environ.get('ADMIN_EMAILS', ''))
    MODERATOR_EMAILS = _split_env_list(os.environ.get('MODERATOR_EMAILS', ''))
    ADMIN_TELEGRAMS = _split_env_list(os.environ.get('ADMIN_TELEGRAMS', ''))
    MODERATOR_TELEGRAMS = _split_env_list(os.environ.get('MODERATOR_TELEGRAMS', ''))
