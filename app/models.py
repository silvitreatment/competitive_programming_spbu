from .extensions import db


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")
    author_name = db.Column(db.String(200))

    def __repr__(self) -> str:
        return f"<Article {self.id} {self.title}>"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    name = db.Column(db.String(200))
    role = db.Column(db.String(20), default="user")
    provider = db.Column(db.String(50))
    external_id = db.Column(db.String(255))
    telegram_username = db.Column(db.String(200))
    password_hash = db.Column(db.String(255))

    def __repr__(self) -> str:
        return f"<User {self.id} {self.name}>"
