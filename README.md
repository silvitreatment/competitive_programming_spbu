Competitive Programming Club Website

This is a small educational Flask project - a simple website for storing articles and materials for a competitive programming club. The site supports basic article management through an admin panel.
![telegram-cloud-photo-size-2-5282844121393467952-w](https://github.com/user-attachments/assets/ed9a7bac-ba86-4e97-ad6b-5efd24881ebb)

## Deploy (Nginx + HTTPS)

1) Install: `sudo apt update && sudo apt install nginx certbot python3-certbot-nginx`.
2) Copy `deploy/nginx.conf` to `/etc/nginx/sites-available/competitive_programming_spbu`, adjust `server_name`, SSL cert paths, static path, and upstream port (default assumes app on `127.0.0.1:8080`).
3) Create ACME webroot if using HTTP-01: `sudo mkdir -p /var/www/letsencrypt`.
4) Enable the site: `sudo ln -s /etc/nginx/sites-available/competitive_programming_spbu /etc/nginx/sites-enabled/` then `sudo nginx -t && sudo systemctl reload nginx`.
5) Issue HTTPS cert: `sudo certbot --nginx -d example.com -d www.example.com` (HTTP port 80 must be open). Certbot will refresh the SSL paths in the config automatically.
6) Start the app behind Nginx (e.g., `gunicorn --bind 127.0.0.1:8080 flask_app:app` or via a systemd service).
