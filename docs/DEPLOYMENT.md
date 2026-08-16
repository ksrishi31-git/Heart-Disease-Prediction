# Deployment — HeartGuard AI

Two supported approaches: a **VPS with Docker + Nginx + Let's Encrypt**, or a
**managed cloud platform**.

## Option A — VPS (Ubuntu + Docker)

Architecture:

```
Internet → HTTPS (443) → Nginx → FastAPI (:8000) → PostgreSQL
                └──────── serves the built React frontend
```

1. Provision an Ubuntu 22.04+ VPS with a public IP and a domain name
   pointing to it.
2. Install Docker + Docker Compose.
3. Clone the repository and create `.env`:

   ```bash
   cp .env.example .env
   # generate keys with: cd backend && python -m app.core.encryption --generate-key
   ```

4. Build and start:

   ```bash
   docker compose up --build -d
   ```

   - `db` — PostgreSQL 16 (data in a named volume).
   - `backend` — trains the models on first start (if missing), applies
     Alembic migrations, serves FastAPI on :8000.
   - `frontend` — Nginx serving the React build on :8080, proxying
     `/api` → backend.

5. Set up TLS with Let's Encrypt + Certbot:

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

   Then adapt `nginx/nginx.conf` (replace `DOMAIN`, point at your certs) and
   use it as the site config:

   ```bash
   sudo cp nginx/nginx.conf /etc/nginx/sites-available/heartguard
   sudo ln -s /etc/nginx/sites-available/heartguard /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

6. Flip security settings for production in the backend environment:
   `APP_ENV=production`, `COOKIE_SECURE=true`, restrict `CORS_ORIGINS` to
   your real domain.

### Backups

- Back up the `pgdata` volume with `pg_dump` and **encrypt the dump**
  (`gpg --symmetric` or `openssl enc -aes-256-cbc`).
- Store backups off-server, rotate keys, restrict access, and **test
  restoration** periodically.
- Never commit backups to Git.

## Option B — Managed cloud

| Component | Example providers |
| --- | --- |
| Frontend (static SPA) | Vercel, Netlify, Cloudflare Pages |
| Backend (FastAPI) | Render, Fly.io, AWS App Runner, Azure App Service, GCP Cloud Run |
| Database | Managed PostgreSQL: RDS, Cloud SQL, Neon, Supabase |
| Key management | AWS KMS, Azure Key Vault, GCP KMS |
| TLS | Managed certificates (each platform issues them automatically) |

Steps:

1. Build the frontend (`npm run build`) and deploy `dist/` to your static
   host. Set `VITE_API_URL` to the public API URL.
2. Deploy the backend with a start command such as
   `python -m app.ml.train && uvicorn app.main:app --host 0.0.0.0 --port 8000`.
3. Point `DATABASE_URL` at the managed PostgreSQL.
4. Put `ENCRYPTION_KEY`, `JWT_SECRET_KEY` and `AUDIT_SALT` into the
   platform's secret store (or a KMS-backed secret manager), and have the
   application read them from environment variables.
5. Enable the managed TLS certificate; set `COOKIE_SECURE=true`.

### Trade-offs

| | VPS | Managed cloud |
| --- | --- | --- |
| Cost | Low, fixed | Pay-per-use, can spike |
| Control | Full (OS, nginx, firewall) | Limited to platform knobs |
| Ops effort | You maintain the OS, certs, backups | Platform handles much of it |
| TLS | Certbot / manual | Automatic managed certificates |
| Scaling | Manual (bigger box) | Often automatic |
| Compliance | You own the whole stack | Depends on provider guarantees |

## Environment variables (full list)

See `backend/.env.example` and `.env.example` (root, for Docker).

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string | SQLite locally |
| `ENCRYPTION_KEY` | Base64 32-byte AES key | required |
| `JWT_SECRET_KEY` | JWT signing secret | required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime | 7 |
| `COOKIE_SECURE` | HttpOnly cookies only over HTTPS | false |
| `AUDIT_SALT` | Salt for IP hashing | required |
| `CORS_ORIGINS` | Comma-separated allowed origins | localhost:5173 |
| `RATE_LIMIT_LOGIN` | Login attempts per IP | 5/minute |
| `RATE_LIMIT_REGISTER` | Registrations per IP | 5/minute |
| `RATE_LIMIT_PREDICTION` | Predictions per user | 30/minute |
| `APP_ENV` | `development` vs `production` | development |
