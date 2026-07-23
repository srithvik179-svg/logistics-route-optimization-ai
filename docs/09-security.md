# RoutePilot AI – Security Architecture & Governance

## Security Overview

RoutePilot AI implements a multi-layered security architecture designed to enforce strict data privacy, role-based authorization, request throttling, and complete audit logging across all enterprise logistics operations.

---

## 1. Authentication & Token Management

- **JSON Web Tokens (JWT):** User sessions are authenticated using signed JWT tokens using HMAC-SHA256 encryption.
- **Configurable Expiration:** Token lifespan is controlled via `JWT_EXPIRE_MINUTES` (default 60 minutes).
- **Header Injection:** All protected API endpoints validate tokens via HTTP Authorization headers: `Authorization: Bearer <token>`.

---

## 2. Role-Based Access Control (RBAC)

The security layer enforces 8 granular permission scopes mapped across enterprise user roles:

| Permission Scope | Administrator | Logistics Analyst | Operations Manager | Judge / Viewer |
|:---|:---:|:---:|:---:|:---:|
| `VIEW_DASHBOARD` | ✅ | ✅ | ✅ | ✅ |
| `RUN_OPTIMIZATION` | ✅ | ✅ | ✅ | ❌ |
| `EXPORT_REPORTS` | ✅ | ✅ | ❌ | ❌ |
| `MANAGE_DATASET` | ✅ | ❌ | ❌ | ❌ |
| `VIEW_AUDIT` | ✅ | ❌ | ❌ | ❌ |
| `ADMIN_CONFIG` | ✅ | ❌ | ❌ | ❌ |
| `API_ACCESS` | ✅ | ✅ | ✅ | ✅ |
| `DEMO_ACCESS` | ✅ | ✅ | ✅ | ✅ |

---

## 3. Input Validation & Data Sanitization

- **Pydantic Model Schema Enforcement:** Every API request body is validated against Pydantic model definitions to prevent injection attacks and bad data shapes.
- **Dataset Validation Pipeline (`DatasetValidator`):** Data loaded into `DataRepository` undergoes schema integrity checks, type checking, and boundary verification before processing.
- **Query Filter Sanitization:** Input workspace filters are strictly sanitized before execution against Pandas DataFrames.

---

## 4. API Rate Limiting & Throttling

- **Global Rate Limiting Middleware:** Protects backend ASGI workers against Denial of Service (DoS) and brute-force attempts.
- **Default Limit:** Configurable limit set to **100 requests per minute per IP** (`RATE_LIMIT=100`).
- **Exceeding Limits:** Returns standard `HTTP 429 Too Many Requests` error with `Retry-After` headers.

---

## 5. Security Audit Logging

The `AuditTrailEngine` captures and persists all critical enterprise events into append-only structured logs.

### Logged Parameters
- UTC Timestamp
- User Identity / Token Subject
- Action Executed (`RUN_COST_SIMULATION`, `DATASET_UPLOAD`, etc.)
- Target Resource
- Execution Status (`SUCCESS` / `FAILURE`)
- Client IP Address

### Searchable Audit Trail
Enterprise admins can query active logs via `POST /api/v1/security/audit-trail`.
