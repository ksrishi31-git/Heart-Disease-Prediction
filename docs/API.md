# API Reference — HeartGuard AI

Base URL (development): `http://localhost:8000/api`
Interactive Swagger docs: `http://localhost:8000/docs` (development only)

Authentication uses **HttpOnly cookies** (`access_token`, `refresh_token`),
so API clients should enable a cookie jar (e.g. curl `-c/-b` or axios
`withCredentials: true`).

## Health

### `GET /api/health`
Liveness probe.
```json
{ "status": "healthy", "database": "not_checked", "models": "not_checked", "version": "heart-disease-model-v1" }
```

### `GET /api/health/ready`
Readiness probe — checks database connectivity and that models are loaded.
Returns 503 if either is unavailable.

## Authentication

### `POST /api/auth/register`
Body: `{ "name", "email", "password", "confirm_password" }`
Creates the account and logs the user in (sets cookies). 400 on validation
failures (weak password, duplicate email, mismatch). Rate limited per IP.

### `POST /api/auth/login`
Body: `{ "email", "password" }`
401 on incorrect credentials. Rate limited per IP.

### `POST /api/auth/refresh`
Rotates the refresh token (old one revoked) and sets new cookies. 401 if the
refresh token is missing/expired/revoked.

### `POST /api/auth/logout`
Revokes the refresh token and clears cookies.

### `GET /api/auth/me`
Returns `{ "id", "name", "email", "created_at", "is_active" }`. 401 when not
authenticated.

## Users / profile

### `POST /api/users/change-password`
Body: `{ "old_password", "new_password" }`. Revokes all other sessions.

### `GET /api/users/sessions`
List the user's sessions (refresh tokens), with `revoked` flags.

### `DELETE /api/users/sessions/{id}`
Revoke one session.

### `DELETE /api/users/me`
Permanently delete the account and all associated prediction records.

## Predictions (authenticated, owner-scoped)

### `POST /api/predictions`
Body — **friendly values**, not dataset codes:
```json
{
  "age": 58, "sex": "Male", "cp": "Asymptomatic",
  "trestbps": 145, "chol": 233, "fbs": "Yes",
  "restecg": "Normal", "thalach": 150, "exang": "No",
  "oldpeak": 2.3, "slope": "Flat", "ca": "0 vessels", "thal": "Normal"
}
```
Runs all three models. 422 on invalid ranges/labels, 413 on oversized
payloads, 429 when rate limited, 503 if models are not trained.

Response:
```json
{
  "prediction_id": "3fa85f64-…",
  "created_at": "2026-08-15T06:18:08Z",
  "model_version": "heart-disease-model-v1",
  "models": {
    "logistic_regression": { "prediction": 1, "probability": 0.70, "label": "Positive" },
    "decision_tree":       { "prediction": 1, "probability": 1.00, "label": "Positive" },
    "random_forest":       { "prediction": 1, "probability": 0.56, "label": "Positive" }
  },
  "consensus": "Positive",
  "consensus_count": "3 of 3",
  "best_model": "logistic_regression",
  "best_model_name": "Logistic Regression"
}
```

### `GET /api/predictions?limit=20&offset=0`
Summary list (non-sensitive fields only) for the authenticated user.

### `GET /api/predictions/{prediction_id}`
Full detail for the owner: adds `input_features` (decrypted) and
`model_version`. 404 for other users' records.

### `DELETE /api/predictions/{prediction_id}`
Delete one of the user's own predictions. 404 if not found / not owned.

### `GET /api/predictions/stats`
Dashboard aggregates for the owner: `{ total_predictions, positive, negative,
latest }`.

## Models

### `GET /api/models`
List all three models with their evaluated metrics + feature importance.

### `GET /api/models/comparison`
Full comparison payload (version, training date, dataset info, per-model
metrics with confusion matrices and ROC curves, best model).

### `GET /api/models/{model_name}/metrics`
Metrics for one model, e.g. `/api/models/logistic_regression/metrics`.

### `GET /api/models/features`
Feature metadata (labels, units, ranges, options) that drives the form.

## Error format

All errors return JSON: `{ "detail": "human-readable message" }`.
- 401 — not authenticated / session expired
- 404 — resource not found (or not owned)
- 422 — validation failed
- 429 — rate limited
- 413 — payload too large
- 503 — service not ready (models missing)

Stack traces and internal details are never returned.
