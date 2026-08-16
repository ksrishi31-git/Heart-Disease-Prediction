# Architecture — HeartGuard AI

## 1. High-level diagram

```
        ┌─────────────────────────────────────────────────────┐
        │                      User / Browser                 │
        └───────────────────────┬─────────────────────────────┘
                                │ HTTPS / TLS 1.2+
                                ▼
        ┌─────────────────────────────────────────────────────┐
        │                  Nginx (reverse proxy)              │
        │   • TLS termination, HTTP→HTTPS redirect, HSTS      │
        │   • serves the built React app (SPA)                │
        │   • proxies /api → FastAPI                          │
        └───────────────────────┬─────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────┐
        │                    FastAPI backend                  │
        │  ┌──────────┐ ┌──────────────┐ ┌─────────────────┐  │
        │  │ Auth API │ │ Prediction   │ │ Models / Health │  │
        │  │ JWT +    │ │ API (rate    │ │ API             │  │
        │  │ Argon2id │ │ limited)     │ │                 │  │
        │  └────┬─────┘ └──────┬───────┘ └────────┬────────┘  │
        │       │              │                   │          │
        │       ▼              ▼                   ▼          │
        │  ┌───────────────────────────────────────────────┐  │
        │  │  Prediction Service → ModelManager            │  │
        │  │  • decrypts models in memory (AES-256-GCM)    │  │
        │  │  • runs all 3 scikit-learn pipelines          │  │
        │  │  • encrypts input + result before storing     │  │
        │  └──────────────────────┬────────────────────────┘  │
        └─────────────────────────┼───────────────────────────┘
                                  │
                          ┌───────▼────────┐
                          │   PostgreSQL   │
                          │  (SQLAlchemy   │
                          │   ORM + Alembic│
                          │   migrations)  │
                          └────────────────┘
```

## 2. Data flow — a prediction request

```
1. User fills the friendly form (labels, not dataset codes)
2. Frontend validates locally (UX only)
3. POST /api/predictions over HTTPS, HttpOnly cookies attached
4. FastAPI: rate limit check → auth (JWT access token) → Pydantic validation
5. Backend maps friendly values → dataset encodings (authoritative validation)
6. ModelManager decrypts the three model files in memory (cached at startup)
7. Same fitted preprocessing transforms the new row (no data leakage)
8. All three models predict → probabilities generated
9. Result + patient input are AES-256-GCM encrypted
10. Encrypted record + non-sensitive summary fields stored in PostgreSQL
11. Audit log entry written; response returned to the frontend
12. Frontend renders consensus + per-model results
```

## 3. Training pipeline

```
heart.csv
   │ load, drop duplicates (302 rows)
   ▼
train/test split (80/20, stratified, random_state=42)
   ▼
ColumnTransformer (StandardScaler + OneHotEncoder) fitted on TRAIN ONLY
   ▼
LogisticRegression ┐
DecisionTree       ├─ each inside a sklearn Pipeline
RandomForest       ┘
   ▼
evaluate on TEST → accuracy, precision, recall, F1, ROC-AUC,
                   confusion matrix, ROC curve, feature importance
   ▼
metrics.json (consumed by the Model Comparison dashboard)
   ▼
joblib serialize → AES-256-GCM encrypt → encrypted_models/*.enc
```

## 4. Backend module map

| Module | Responsibility |
| --- | --- |
| `app/main.py` | App factory, lifespan (migrations, model loading), middleware, error handlers |
| `app/api/*` | HTTP routers: auth, users, predictions, models, health |
| `app/core/config.py` | All configuration from environment variables |
| `app/core/security.py` | JWT creation/validation, Argon2id password hashing |
| `app/core/encryption.py` | AES-256-GCM encrypt/decrypt (data + files) |
| `app/core/logging_config.py` | Structured JSON logging |
| `app/db/` | SQLAlchemy engine, ORM models, Pydantic schemas, seed data |
| `app/ml/` | Preprocessing, training, evaluation, prediction, ModelManager |
| `app/services/` | Business logic: auth, predictions, models, audit |
| `app/utils/` | Validators, IP hashing |

## 5. Frontend module map

| Module | Responsibility |
| --- | --- |
| `src/main.jsx` | React root + providers |
| `src/App.jsx` | Route table (public vs protected) |
| `src/layouts/` | AppLayout (nav), AuthLayout |
| `src/pages/` | Landing, Login, Register, Dashboard, Predict, History, ModelComparison, Security |
| `src/services/` | Axios client + API functions |
| `src/hooks/useAuth.jsx` | Auth context (session, login, logout, refresh) |
| `src/utils/` | Form validation (mirrors backend), formatting |
| `src/components/` | Cards, forms, charts, badges, stat cards |

## 6. Key design decisions

- **SQLite locally, PostgreSQL in production** — the same SQLAlchemy code
  runs on both; only `DATABASE_URL` changes.
- **Migrations everywhere** — the app applies `alembic upgrade head` at
  startup, so a fresh clone just works.
- **Encryption at rest + encrypted model files** — sensitive data is never
  stored in plaintext, and models are decrypted only in memory.
- **HttpOnly cookies for tokens** — JavaScript never sees the JWT, which
  defeats XSS token theft. Refresh tokens are rotated and revocable.
- **Backend validation is authoritative** — frontend validation is a UX
  convenience only.
