from app import create_app

app = create_app()


def _ssl_context():
    """Return SSL context tuple/flag if HTTPS is configured via env vars."""
    cert_path = app.config.get("SSL_CERT_PATH")
    key_path = app.config.get("SSL_KEY_PATH")
    if cert_path and key_path:
        return (cert_path, key_path)
    if app.config.get("SSL_ADHOC"):
        return "adhoc"
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080, ssl_context=_ssl_context())
