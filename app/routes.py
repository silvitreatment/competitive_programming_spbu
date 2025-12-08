from flask import abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import require_login, require_roles, set_current_user
from .extensions import db
from .models import Article, User


def register_routes(app) -> None:
    @app.route("/articles/new")
    @require_login
    def new_article():
        return render_template("new_article.html")

    @app.route("/articles/<int:article_id>/delete", methods=["POST"])
    @require_roles("admin")
    def delete_article(article_id):
        article = Article.query.get_or_404(article_id)
        db.session.delete(article)
        db.session.commit()
        flash("The article is deleted")
        return redirect(url_for("index"))

    @app.route("/articles", methods=["POST"])
    @require_login
    def create_article():
        title = request.form["title"]
        content = request.form["content"]

        status = "published" if g.current_user and g.current_user.role in ("moderator", "admin") else "pending"
        author_name = g.current_user.name if g.current_user else None

        new_article = Article(title=title, content=content, status=status, author_name=author_name)
        db.session.add(new_article)
        db.session.commit()

        flash("Материал отправлен на модерацию" if status == "pending" else "Новая статья опубликована")

        return redirect(url_for("index"))

    @app.route("/articles/<int:article_id>/edit")
    @require_roles("moderator", "admin")
    def edit_article(article_id):
        article = Article.query.get_or_404(article_id)
        return render_template("edit_article.html", article=article)

    @app.route("/articles/<int:article_id>/update", methods=["POST"])
    @require_roles("moderator", "admin")
    def update_article(article_id):
        article = Article.query.get_or_404(article_id)
        article.title = request.form["title"]
        article.content = request.form["content"]
        db.session.commit()
        flash("Changes are saved")
        return redirect(url_for("show_article", article_id=article.id))

    @app.route("/articles/<int:article_id>")
    def show_article(article_id):
        article = Article.query.get_or_404(article_id)
        if article.status != "published" and (not g.current_user or g.current_user.role not in ("moderator", "admin")):
            abort(404)
        return render_template("article_detail.html", article=article)

    @app.route("/")
    def index():
        query = Article.query.order_by(Article.id.desc())
        if not g.current_user or g.current_user.role == "user":
            articles = query.filter_by(status="published").all()
        else:
            articles = query.all()
        pending = (
            Article.query.filter_by(status="pending").order_by(Article.id.desc()).all()
            if g.current_user and g.current_user.role in ("moderator", "admin")
            else []
        )
        return render_template("index.html", articles=articles, pending_articles=pending)

    @app.route("/articles")
    def articles_feed():
        query = Article.query.order_by(Article.id.desc())
        if not g.current_user or g.current_user.role == "user":
            articles = query.filter_by(status="published").all()
        else:
            articles = query.all()
        return render_template("articles_feed.html", articles=articles)

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contacts")
    def contacts():
        contacts_data = [
            {
                "initials": "НК",
                "name": "Никита К.",
                "role": "Руководитель кружка",
                "about": "Куратор программы, встречи и стратегическое развитие.",
                "telegram": "#",
                "email": "nikita@example.com",
            },
            {
                "initials": "ЕМ",
                "name": "Екатерина М.",
                "role": "Методист",
                "about": "Помогает с конспектами, редактурой и практическими материалами.",
                "telegram": "#",
                "email": "kate@example.com",
            },
            {
                "initials": "АС",
                "name": "Алексей С.",
                "role": "Ментор по задачам",
                "about": "Разборы олимпиад, менторство и подготовка к интервью.",
                "telegram": "#",
                "email": "alex@example.com",
            },
            {
                "initials": "ВД",
                "name": "Влада Д.",
                "role": "Дизайн и контент",
                "about": "Визуал, UX и поддержка базы знаний в актуальном виде.",
                "telegram": "#",
                "email": "vlad@example.com",
            },
        ]
        return render_template("contacts.html", contacts=contacts_data)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST" and request.form.get("login_method") == "password":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            user = User.query.filter_by(provider="local", external_id=username).first()

            if user and user.password_hash and check_password_hash(user.password_hash, password):
                set_current_user(user)
                flash("Вы вошли по логину и паролю")
                return redirect(url_for("index"))

            if username == current_app.config["ADMIN_USERNAME"] and password == current_app.config["ADMIN_PASSWORD"]:
                if not user:
                    user = User(
                        email=None,
                        name=username,
                        provider="local",
                        external_id=username,
                        role="admin",
                        password_hash=generate_password_hash(password),
                    )
                    db.session.add(user)
                else:
                    user.role = "admin"
                    user.password_hash = generate_password_hash(password)
                db.session.commit()
                set_current_user(user)
                flash("Вы вошли как админ")
                return redirect(url_for("index"))

            error = "Неверное имя пользователя или пароль"

        return render_template("login.html", error=error)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            name = request.form.get("name", "").strip() or username
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")
            if not username or not password:
                error = "Заполните все поля"
            elif password != confirm:
                error = "Пароли не совпадают"
            elif User.query.filter_by(provider="local", external_id=username).first():
                error = "Такой пользователь уже существует"
            else:
                user = User(
                    name=name,
                    provider="local",
                    external_id=username,
                    role="user",
                    password_hash=generate_password_hash(password),
                )
                db.session.add(user)
                db.session.commit()
                set_current_user(user)
                flash("Регистрация прошла успешно")
                return redirect(url_for("index"))

        return render_template("register.html", error=error)

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("role", None)
        flash("Вы вышли из системы")
        return redirect(url_for("index"))

    @app.route("/articles/<int:article_id>/publish", methods=["POST"])
    @require_roles("moderator", "admin")
    def publish_article(article_id):
        article = Article.query.get_or_404(article_id)
        article.status = "published"
        db.session.commit()
        flash("Статья опубликована")
        return redirect(url_for("show_article", article_id=article.id))
