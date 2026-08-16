# Security — HeartGuard AI

This document describes exactly what security mechanisms exist, how they
work, and — just as importantly — what they do **not** guarantee.

## 1. Transport security (TLS)

- Production deployments must use **HTTPS with TLS 1.2 or 1.3** (see
  `nginx/nginx.conf` and `docs/DEPLOYMENT.md`).
- Nginx terminates TLS, redirects HTTP → HTTPS and sends
  `Strict-Transport-Security` (HSTS).
- Self-signed certificates are never used in production; use Let's Encrypt +
  Certbot on a VPS, or a managed certificate on a cloud platform.
- **Honest limitation:** TLS encrypts communication *between client and
  server*. That is transport security, not true end-to-end encryption — the
  server can read the data. Real client-side E2EE would require the server to
  be unable to decrypt the payload, which is incompatible with server-side ML
  inference (unless privacy-preserving ML such as homomorphic encryption is
  used, which is out of scope here).

## 2. Encryption at rest (AES-256-GCM)

- Sensitive fields — patient input and full prediction results — are
  encrypted with **AES-256-GCM** (the `cryptography` library) before being
  written to the database.
- Every encryption uses a **fresh random 12-byte nonce**; the tag authenticates
  the ciphertext, so tampering is detected.
- Non-sensitive summary fields (consensus label, best model, probability,
  dates) stay plaintext so history lists can be served without decrypting
  everything.
- The key comes from `ENCRYPTION_KEY` (base64, 32 bytes). It is never
  hardcoded, never exposed to the frontend, and never returned by an API.

## 3. Encrypted model files

- Trained models are serialized with joblib, encrypted with AES-256-GCM and
  stored in `encrypted_models/*.enc`.
- At startup `ModelManager` decrypts each file **in memory** and caches the
  pipeline. Plaintext model artifacts are never written to disk at runtime.
- Only models produced by the trusted training pipeline (listed in
  `registry.json`) are loaded. The application never deserializes
  user-uploaded files, so untrusted pickle/joblib payloads cannot be
  executed.

## 4. Key management

- Local development: environment variables (see `backend/.env.example`).
- Production: read the same variables from a cloud KMS — AWS KMS, Azure Key
  Vault or Google Cloud KMS. The application is provider-agnostic: it only
  consumes a `ENCRYPTION_KEY` value, so the storage/retrieval mechanism can
  be swapped without code changes.
- `.env` files are gitignored and never committed.

## 5. Authentication

- Passwords are hashed with **Argon2id** (memory-hard, recommended by OWASP).
  Plaintext passwords are never stored.
- **JWT access tokens** (short expiry, default 15 minutes) and **refresh
  tokens** (default 7 days) are delivered as **HttpOnly, SameSite=Lax
  cookies** — JavaScript cannot read them, which mitigates XSS token theft.
- Refresh tokens are **rotated** on every use (the old one is revoked) and
  stored as SHA-256 hashes in the database, so a leaked database cannot be
  used to forge sessions. Sessions can be revoked individually or globally
  (password change revokes all).
- `COOKIE_SECURE=true` must be set behind HTTPS so cookies are only sent over
  TLS.

## 6. Authorization

- Every prediction is owned by a user; list/detail/delete endpoints always
  filter by the authenticated user's id. Accessing another user's record
  returns 404 (it does not reveal that the record exists).
- Protected routes on the frontend redirect unauthenticated users to login.

## 7. Input validation

- Pydantic validates request shape at the API boundary.
- Business rules (feature ranges, allowed categorical values, password
  strength, email format) are enforced in the backend and are authoritative.
- The frontend mirrors these rules for UX, but never trusts them.
- Request bodies larger than 50 KB are rejected (413).

## 8. Rate limiting

- Login / registration: 5 attempts/minute per IP (configurable) — brute-force
  protection.
- Predictions: 30 requests/minute per authenticated user (configurable).

## 9. Security headers & CORS

- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy`, HSTS (HTTPS only)
  and a Content-Security-Policy (HTTPS only).
- CORS allows only configured origins (never `*` with credentials).

## 10. Logging & audit

- Structured JSON logs record auth events, prediction success/failure, model
  loading and server errors — but never passwords, keys, or decrypted health
  data.
- An `audit_logs` table records login, failed login, logout, registration,
  prediction created, password change and account deletion. IP addresses are
  stored only as salted SHA-256 hashes.

## 11. What this project does NOT claim

- It is **not** "100% secure", "military-grade" or HIPAA/GDPR-compliant.
- Compliance depends on deployment location, applicable law, controller
  responsibilities, consent, retention policies, and legal review — see
  `docs/COMPLIANCE.md` notes in the README.
- Encryption protects data at rest and in transit; it does not make the
  system a certified medical device or a clinical diagnostic tool.

## 12. Hardening checklist (documented, most already implemented)

- [x] HTTPS/TLS 1.2+ config (nginx template + docs)
- [x] HSTS, secure cookies
- [x] CORS restrictions
- [x] Rate limiting (login, register, prediction)
- [x] JWT auth with short-lived access tokens
- [x] Refresh-token rotation + revocation
- [x] Argon2id password hashing
- [x] AES-256-GCM encryption at rest
- [x] Encrypted model files, decrypted only in memory
- [x] Secrets via environment variables, `.env` gitignored
- [x] Input validation (frontend + authoritative backend)
- [x] Structured logging without sensitive data
- [x] Audit logs with hashed IPs
- [x] Payload size limits
- [ ] Database firewall / private networking (deployment concern)
- [ ] Dependency updates (ongoing)
- [ ] Encrypted backups + tested restoration (see README backup section)
