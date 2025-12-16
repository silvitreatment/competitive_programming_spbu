import secrets
from urllib.parse import urlencode, urlparse

import requests
from flask import abort, current_app, flash, g, redirect, render_template, request, session, url_for

from .auth import require_login, require_roles, resolve_role, set_current_user
from .extensions import db
from .models import Article, Comment, Review, User


def register_routes(app) -> None:
    contacts_data = [
        {
            "slug": "daniil",
            "initials": "ДП",
            "name": "Даниил Плотников",
            "role": "Преподаватель кружка",
            "about": "Преподаватель кружка, составитель контестов.",
            "telegram": "https://t.me/PlotDaniil",
            "email": "daniil@gmail.com",
            "photo": "images/daniil.jpg",
            "expertise": ["Лекции", "Контесты", "Материалы для занятий", "Разбор задач"],
        },
        {
            "slug": "kate",
            "initials": "ИЗ",
            "name": "Иван Закарлюка",
            "role": "Преподаватель кружка",
            "about": "Преподаватель кружка, составитель контестов.",
            "telegram": "https://t.me/kamenkremen",
            "email": "kamen@example.com",
            "photo": "images/ivan.jpg",
            "expertise": ["Лекции", "Контесты", "Материалы для занятий", "Разбор задач"],
        },
        {
            "slug": "rey",
            "initials": "РШ",
            "name": "Рафаэль Шойунчап",
            "role": "Преподаватель кружка",
            "about": (
                "Иногда лектор.                      "
                "Немного обо мне: Делал десктоп-приложение для анализа графов (Kotlin + Jetpack Compose + SQLite/Neo4j): "
                "Louvain, Форд–Беллман, MST, визуализация, CI с линтерами и тестами. "
                "Преподаю спортпрогу: теория чисел и др. "
                "Вел смену Импульс для олимпиадников в Вологде от СПбГУ"
            ),
            "telegram": "https://t.me/branch_study",
            "email": "1junyawork@example.com",
            "photo": "images/rafael.jpg",
            "github": "https://github.com/silvitreatment",
            "expertise": ["Лекции", "Материалы для занятий"],
        },
        {
            "slug": "leonid",
            "initials": "ЛР",
            "name": "Леонид Романычев",
            "role": "ex-Преподаватель кружка",
            "about": "Преподаватель кружка, составитель контестов.",
            "telegram": "https://t.me/romanychev",
            "email": "romanychev@example.com",
            "photo": "images/leonid.jpg",
            "expertise": ["Лекции", "Контесты", "Материалы для занятий", "Разбор задач"],
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

    def safe_next_url(value: str | None) -> str | None:
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            if parsed.netloc != request.host:
                return None
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            return path
        return value or "/"

    @app.route("/login")
    def login():
        next_url = safe_next_url(request.args.get("next") or request.referrer)
        if g.current_user:
            return redirect(next_url or url_for("index"))
        return render_template("login.html", next_url=next_url)

    @app.route("/login/google")
    def login_with_google():
        client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            flash("Google OAuth не настроен. Задайте GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET.")
            return redirect(url_for("login"))

        state = secrets.token_urlsafe(16)
        session["oauth_state"] = state
        next_url = safe_next_url(request.args.get("next") or request.args.get("redirect"))
        if next_url:
            session["oauth_next"] = next_url

        redirect_uri = url_for("google_auth_callback", _external=True)
        params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": redirect_uri,
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))

    @app.route("/login/yandex")
    def login_with_yandex():
        client_id = current_app.config.get("YANDEX_CLIENT_ID")
        client_secret = current_app.config.get("YANDEX_CLIENT_SECRET")
        if not client_id or not client_secret:
            flash("Яндекс OAuth не настроен. Задайте YANDEX_CLIENT_ID и YANDEX_CLIENT_SECRET.")
            return redirect(url_for("login"))

        state = secrets.token_urlsafe(16)
        session["oauth_state"] = state
        next_url = safe_next_url(request.args.get("next") or request.args.get("redirect"))
        if next_url:
            session["oauth_next"] = next_url

        redirect_uri = url_for("yandex_auth_callback", _external=True)
        scope = (current_app.config.get("YANDEX_SCOPE") or "").strip()
        if not scope:
            scope = current_app.config.get("YANDEX_SCOPE_DEFAULT", "")
        current_app.logger.info("Using Yandex scope: %s", scope)
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "force_confirm": "yes",
        }
        return redirect("https://oauth.yandex.ru/authorize?" + urlencode(params))

    @app.route("/auth/google/callback")
    def google_auth_callback():
        if request.args.get("error"):
            flash("Не удалось войти через Google.")
            return redirect(url_for("login"))

        client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            flash("Google OAuth не настроен. Задайте GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET.")
            return redirect(url_for("login"))

        state = request.args.get("state")
        if not state or state != session.get("oauth_state"):
            abort(400)

        code = request.args.get("code")
        if not code:
            flash("Google не вернул код авторизации.")
            return redirect(url_for("login"))

        try:
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": url_for("google_auth_callback", _external=True),
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
        except requests.RequestException:
            flash("Не удалось обратиться к Google для обмена кода.")
            return redirect(url_for("login"))
        if not token_resp.ok:
            flash("Не удалось получить токен от Google.")
            return redirect(url_for("login"))

        access_token = token_resp.json().get("access_token")
        if not access_token:
            flash("Ответ Google не содержит токена.")
            return redirect(url_for("login"))

        try:
            profile_resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
        except requests.RequestException:
            flash("Не удалось получить профиль Google.")
            return redirect(url_for("login"))
        if not profile_resp.ok:
            flash("Не удалось получить профиль Google.")
            return redirect(url_for("login"))

        profile = profile_resp.json()
        email = profile.get("email")
        external_id = profile.get("sub")
        name = profile.get("name") or (email.split("@")[0] if email else None)

        if not email or not external_id:
            flash("Google не прислал email или идентификатор пользователя.")
            return redirect(url_for("login"))

        user = User.query.filter_by(provider="google", external_id=external_id).first()
        if not user and email:
            user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                name=name,
                provider="google",
                external_id=external_id,
                role=resolve_role(email=email),
            )
            db.session.add(user)
        else:
            user.email = email
            user.name = name
            user.provider = "google"
            user.external_id = external_id
            user.role = resolve_role(email=email)

        db.session.commit()
        set_current_user(user)
        session.pop("oauth_state", None)

        flash("Вы вошли через Google")
        next_url = session.pop("oauth_next", None)
        return redirect(next_url or url_for("index"))

    @app.route("/auth/yandex/callback")
    def yandex_auth_callback():
        if request.args.get("error"):
            flash("Не удалось войти через Яндекс.")
            return redirect(url_for("login"))

        client_id = current_app.config.get("YANDEX_CLIENT_ID")
        client_secret = current_app.config.get("YANDEX_CLIENT_SECRET")
        if not client_id or not client_secret:
            flash("Яндекс OAuth не настроен. Задайте YANDEX_CLIENT_ID и YANDEX_CLIENT_SECRET.")
            return redirect(url_for("login"))

        state = request.args.get("state")
        if not state or state != session.get("oauth_state"):
            abort(400)

        code = request.args.get("code")
        if not code:
            flash("Яндекс не вернул код авторизации.")
            return redirect(url_for("login"))

        try:
            token_resp = requests.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=10,
            )
        except requests.RequestException:
            flash("Не удалось обратиться к Яндексу для обмена кода.")
            return redirect(url_for("login"))
        if not token_resp.ok:
            flash("Не удалось получить токен от Яндекса.")
            return redirect(url_for("login"))

        access_token = token_resp.json().get("access_token")
        if not access_token:
            flash("Ответ Яндекса не содержит токена.")
            return redirect(url_for("login"))

        try:
            profile_resp = requests.get(
                "https://login.yandex.ru/info",
                params={"format": "json"},
                headers={"Authorization": f"OAuth {access_token}"},
                timeout=10,
            )
        except requests.RequestException:
            flash("Не удалось получить профиль Яндекса.")
            return redirect(url_for("login"))
        if not profile_resp.ok:
            flash("Не удалось получить профиль Яндекса.")
            return redirect(url_for("login"))

        profile = profile_resp.json()
        external_id = profile.get("id") or profile.get("psuid")
        emails = profile.get("emails") or []
        email = profile.get("default_email") or (emails[0] if emails else None)
        name = profile.get("real_name") or profile.get("display_name") or (email.split("@")[0] if email else None)

        if not external_id:
            flash("Яндекс не прислал идентификатор пользователя.")
            return redirect(url_for("login"))

        user = User.query.filter_by(provider="yandex", external_id=external_id).first()
        if not user and email:
            user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                name=name or "Пользователь Яндекса",
                provider="yandex",
                external_id=external_id,
                role=resolve_role(email=email),
            )
            db.session.add(user)
        else:
            user.email = email
            user.name = name or user.name
            user.provider = "yandex"
            user.external_id = external_id
            user.role = resolve_role(email=email)

        db.session.commit()
        set_current_user(user)
        session.pop("oauth_state", None)

        flash("Вы вошли через Яндекс")
        next_url = session.pop("oauth_next", None)
        return redirect(next_url or url_for("index"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        flash("Регистрация по логину и паролю отключена. Используйте вход через Google или Яндекс.")
        return redirect(url_for("login"))

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("role", None)
        session.pop("logged_in", None)
        session.pop("oauth_state", None)
        session.pop("oauth_next", None)
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
