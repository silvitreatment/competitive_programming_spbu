from flask import abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import require_login, require_roles, set_current_user
from .extensions import db
from .models import Article, Comment, Review, User


def register_routes(app) -> None:
    contacts_data = [
        {
            "slug": "nikita",
            "initials": "НК",
            "name": "Никита К.",
            "role": "Руководитель кружка",
            "about": "Куратор программы, встречи и стратегическое развитие.",
            "telegram": "#",
            "email": "nikita@example.com",
            "photo": "https://placehold.co/640x360/0f172a/e2e8f0?text=Никита",
            "expertise": ["Олимпиады", "Стратегия кружка", "1:1 менторство"],
        },
        {
            "slug": "kate",
            "initials": "ЕМ",
            "name": "Екатерина М.",
            "role": "Методист",
            "about": "Помогает с конспектами, редактурой и практическими материалами.",
            "telegram": "#",
            "email": "kate@example.com",
            "photo": "https://placehold.co/640x360/312e81/e0e7ff?text=Екатерина",
            "expertise": ["Редактура", "Конспекты", "Материалы для занятий"],
        },
        {
            "slug": "alex",
            "initials": "АС",
            "name": "Алексей С.",
            "role": "Ментор по задачам",
            "about": "Разборы олимпиад, менторство и подготовка к интервью.",
            "telegram": "#",
            "email": "alex@example.com",
            "photo": "https://placehold.co/640x360/0c4a6e/cbd5e1?text=Алексей",
            "expertise": ["Разбор задач", "Интервью", "Алгоритмы"],
        },
        {
            "slug": "vlada",
            "initials": "ВД",
            "name": "Влада Д.",
            "role": "Дизайн и контент",
            "about": "Визуал, UX и поддержка базы знаний в актуальном виде.",
            "telegram": "#",
            "email": "vlad@example.com",
            "photo": "https://placehold.co/640x360/1e293b/e2e8f0?text=Влада",
            "expertise": ["UX", "Визуал", "Контент"],
        },
    ]

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
        if g.current_user and g.current_user.role in ("moderator", "admin"):
            comments = Comment.query.filter_by(article_id=article.id).order_by(Comment.id.desc()).all()
        else:
            comments = (
                Comment.query.filter_by(article_id=article.id, status="published")
                .order_by(Comment.id.desc())
                .all()
            )
        return render_template("article_detail.html", article=article, comments=comments)

    @app.route("/articles/<int:article_id>/comments", methods=["POST"])
    @require_login
    def add_comment(article_id):
        article = Article.query.get_or_404(article_id)
        content = request.form.get("content", "").strip()
        if not content:
            flash("Комментарий не может быть пустым")
            return redirect(url_for("show_article", article_id=article.id))

        author_name = g.current_user.name if g.current_user else None
        comment = Comment(article_id=article.id, content=content, author_name=author_name, status="pending")
        db.session.add(comment)
        db.session.commit()
        flash("Комментарий отправлен на модерацию")
        return redirect(url_for("show_article", article_id=article.id))

    @app.route("/comments/<int:comment_id>/publish", methods=["POST"])
    @require_roles("moderator", "admin")
    def publish_comment(comment_id):
        comment = Comment.query.get_or_404(comment_id)
        comment.status = "published"
        db.session.commit()
        flash("Комментарий опубликован")
        return redirect(url_for("show_article", article_id=comment.article_id))

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
        return render_template("contacts.html", contacts=contacts_data)

    @app.route("/contacts/<slug>")
    def contact_detail(slug):
        person = next((p for p in contacts_data if p["slug"] == slug), None)
        if not person:
            abort(404)
        if g.current_user and g.current_user.role in ("moderator", "admin"):
            reviews = Review.query.filter_by(contact_slug=slug).order_by(Review.id.desc()).all()
        else:
            reviews = (
                Review.query.filter_by(contact_slug=slug, status="published").order_by(Review.id.desc()).all()
            )
        return render_template("contact_detail.html", person=person, reviews=reviews)

    @app.route("/contacts/<slug>/reviews", methods=["POST"])
    @require_login
    def add_review(slug):
        person = next((p for p in contacts_data if p["slug"] == slug), None)
        if not person:
            abort(404)
        content = request.form.get("content", "").strip()
        if not content:
            flash("Отзыв не может быть пустым")
            return redirect(url_for("contact_detail", slug=slug))
        author_name = g.current_user.name if g.current_user else None
        review = Review(contact_slug=slug, content=content, author_name=author_name, status="pending")
        db.session.add(review)
        db.session.commit()
        flash("Отзыв отправлен на модерацию")
        return redirect(url_for("contact_detail", slug=slug))

    @app.route("/reviews/<int:review_id>/publish", methods=["POST"])
    @require_roles("moderator", "admin")
    def publish_review(review_id):
        review = Review.query.get_or_404(review_id)
        review.status = "published"
        db.session.commit()
        flash("Отзыв опубликован")
        return redirect(url_for("contact_detail", slug=review.contact_slug))

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
