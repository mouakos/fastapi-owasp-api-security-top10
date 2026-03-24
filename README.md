<div align="center">

# FastAPI OWASP API Security Top 10

A production-style FastAPI project built to demonstrate practical defenses for the **OWASP API Security Top 10 (2023)**.

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-production-green)](https://fastapi.tiangolo.com/)
[![SQLModel](https://img.shields.io/badge/SQLModel-ORM-blueviolet)](https://sqlmodel.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-package_manager-DE5FE9)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-pytest-informational)](https://docs.pytest.org/)
[![OWASP](https://img.shields.io/badge/OWASP-API_Top_10_(2023)-red)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## 📋 Table of Contents

- [FastAPI OWASP API Security Top 10](#fastapi-owasp-api-security-top-10)
  - [📋 Table of Contents](#-table-of-contents)
  - [🔍 Overview](#-overview)
  - [🛠️ Tech stack](#️-tech-stack)
  - [🔐 OWASP API Top 10 coverage](#-owasp-api-top-10-coverage)
  - [📁 Project structure](#-project-structure)
  - [🚀 Getting started](#-getting-started)
    - [Local setup](#local-setup)
    - [Environment variables](#environment-variables)
    - [Run with Docker](#run-with-docker)
  - [🔌 API reference](#-api-reference)
    - [Endpoints](#endpoints)
    - [Example workflow](#example-workflow)
  - [🧪 Testing](#-testing)
  - [🔬 Code quality](#-code-quality)
  - [🛡️ Security](#️-security)
  - [📚 Further reading](#-further-reading)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)

---

## 🔍 Overview

This project is a hands-on reference implementation of the **OWASP API Security Top 10 (2023)** built with FastAPI. Each security risk is addressed with concrete, working code.

The API manages users and items with authentication, role-based access control, pagination, and an external URL import feature. Every layer — router, schema, service, middleware — carries an explicit OWASP reference so you can trace each security control back to the risk it mitigates.

Key areas covered:

- **Authentication & authorization** — JWT tokens, protected dependencies, role-based admin access
- **Resource protection** — rate limiting per IP, request body size cap, paginated responses
- **SSRF prevention** — user-supplied URLs are validated before any outbound call is made
- **Safe consumption** — external API responses are parsed through strict Pydantic schemas before entering the system
- **Observability** — structured logs with per-request correlation IDs and security headers on every response
- **Clean architecture** — API, service, persistence, and unit-of-work layers are clearly separated and independently testable

---

## 🛠️ Tech stack

| Layer                | Technology                                                                          |
| -------------------- | ----------------------------------------------------------------------------------- |
| Framework            | [FastAPI](https://fastapi.tiangolo.com/)                                            |
| ORM & validation     | [SQLModel](https://sqlmodel.tiangolo.com/) + [Pydantic](https://docs.pydantic.dev/) |
| Database             | PostgreSQL (production) · SQLite (local dev)                                        |
| Migrations           | [Alembic](https://alembic.sqlalchemy.org/)                                          |
| Authentication       | JWT via [PyJWT](https://pyjwt.readthedocs.io/) · Argon2 password hashing            |
| Logging              | [Loguru](https://loguru.readthedocs.io/) — structured, with correlation IDs         |
| Rate limiting        | [SlowAPI](https://slowapi.readthedocs.io/)                                          |
| Testing              | [Pytest](https://docs.pytest.org/) + [HTTPX](https://www.python-httpx.org/)         |
| Linting & formatting | [Ruff](https://docs.astral.sh/ruff/)                                                |
| Type checking        | [Mypy](https://mypy.readthedocs.io/) (strict mode)                                  |
| Runtime              | Python 3.13 · [uv](https://docs.astral.sh/uv/)                                      |

---

## 🔐 OWASP API Top 10 coverage

| #     | Category                                        | Implementation                                               |
| ----- | ----------------------------------------------- | ------------------------------------------------------------ |
| API1  | Broken Object Level Authorization               | Item operations are always scoped to the authenticated owner |
| API2  | Broken Authentication                           | JWT validation with protected FastAPI dependencies           |
| API3  | Broken Object Property Level Authorization      | Patch schemas restrict what users can modify (role excluded) |
| API4  | Unrestricted Resource Consumption               | Rate limiting per IP, body-size limit, page-size cap         |
| API5  | Broken Function Level Authorization             | Admin endpoints require admin role via dependency            |
| API6  | Unrestricted Access to Sensitive Business Flows | Rate-limited login/register with account lockout             |
| API7  | Server Side Request Forgery                     | URL validation before any outbound fetch                     |
| API8  | Security Misconfiguration                       | Strict CORS, security headers, docs hidden in production     |
| API9  | Improper Inventory Management                   | Single versioned router under `/api/v1`                      |
| API10 | Unsafe Consumption of APIs                      | External payloads validated through strict Pydantic schemas  |

---

## 📁 Project structure

```text
.
├── app/
│   ├── main.py                   # App factory, middleware stack, lifespan
│   ├── api/
│   │   ├── deps.py               # Dependency injection (auth, pagination, services)
│   │   ├── middleware.py         # Security headers & request logging
│   │   ├── exception_handlers.py # Centralised error responses
│   │   └── v1/
│   │       ├── router.py         # Versioned router composition
│   │       ├── endpoints/        # auth · users · items · admin handlers
│   │       └── schemas/          # Pydantic request/response models
│   ├── core/
│   │   ├── config.py             # Settings from environment variables
│   │   ├── exceptions.py         # Shared domain exceptions
│   │   ├── logging.py            # Loguru setup and log patching
│   │   └── security/
│   │       ├── jwt.py            # Token creation and decoding
│   │       └── password.py       # Argon2 hashing and verification
│   ├── persistence/
│   │   ├── database.py           # Async engine and session factory
│   │   ├── models/               # SQLModel ORM models (User, Item)
│   │   ├── repositories/         # Repository interfaces + SQLModel implementations
│   │   └── uow/                  # Unit of work pattern
│   ├── services/
│   │   ├── user_service.py       # Auth, lockout, RBAC logic
│   │   └── item_service.py       # Item ownership enforcement
│   └── utils/
│       ├── http_client.py        # Typed outbound HTTP helper
│       ├── ssrf.py               # SSRF URL validation (API7)
│       └── time.py               # UTC time utilities
├── tests/
│   ├── unit/                     # Unit tests — services, utils, core
│   ├── integration/              # Repository and database integration tests
│   └── api/                      # Full API tests via HTTPX async client
├── alembic/                      # Database migrations
├── scripts/
│   └── prestart.py               # Runs migrations and seeds first admin on startup
├── Dockerfile                    # Multi-stage build (builder + slim runtime, non-root user)
├── docker-compose.yml            # API + PostgreSQL 17 services
└── pyproject.toml                # Dependencies, Ruff, Mypy, Pytest config
```

---

## 🚀 Getting started

### Local setup

**Prerequisites:** Python 3.13+ and [uv](https://docs.astral.sh/uv/)

1. Clone the repository

```bash
git clone https://github.com/mouakos/fastapi-owasp-api-security-top10.git
cd fastapi-owasp-api-security-top10
```

2. Install dependencies

```bash
uv sync --dev
```

3. Create your environment file and fill in the required values (see [Environment variables](#environment-variables) below)

```bash
cp .env.example .env          # macOS / Linux
Copy-Item .env.example .env   # Windows PowerShell
```

4. Run migrations and seed initial data

```bash
uv run python scripts/prestart.py
```

5. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`.
Interactive docs are available at `http://localhost:8000/api/v1/docs` (disabled automatically in production).

---

### Environment variables

Copy `.env.example` to `.env` and set the values below. All ✅ rows are required before the app will start.

| Variable               | Required | Default         | Description                                                                                          |
| ---------------------- | :------: | --------------- | ---------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`           |    ✅     | —               | JWT signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"`        |
| `DATABASE_URL`         |    ✅     | —               | `sqlite+aiosqlite:///./dev.db` locally · `postgresql+asyncpg://user:pass@host:5432/db` in production |
| `ENVIRONMENT`          |    ✅     | `development`   | `development` · `staging` · `production` — controls docs exposure and env-specific behaviour         |
| `ALLOWED_ORIGINS`      |    ❌     | localhost ports | Comma-separated CORS origins, e.g. `http://localhost:3000,https://myapp.com`                         |
| `FIRST_ADMIN_EMAIL`    |    ✅     | —               | Email for the seeded admin account                                                                   |
| `FIRST_ADMIN_USERNAME` |    ✅     | —               | Username for the seeded admin account                                                                |
| `FIRST_ADMIN_PASSWORD` |    ✅     | —               | Password for the seeded admin account (min 8 chars, uppercase, digit, symbol)                        |
| `LOG_LEVEL`            |    ❌     | `INFO`          | `DEBUG` · `INFO` · `WARNING` · `ERROR` · `CRITICAL`                                                  |
| `LOG_SERIALIZED`       |    ❌     | `False`         | `True` emits JSON logs — useful for log aggregators (Datadog, ELK, Loki)                             |
| `LOG_TO_FILE`          |    ❌     | `False`         | Write logs to a file — keep `False` in containers                                                    |

---

### Run with Docker

The project ships a multi-stage `Dockerfile` (slim runtime, non-root user) and a `docker-compose.yml` that starts both the **FastAPI application** and a **PostgreSQL 17** database.

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

1. Create and configure your `.env` file as described [above](#environment-variables)

2. Build and start all services

```bash
docker compose up --build
```

> On first start, the container automatically runs Alembic migrations and seeds the initial admin account before Uvicorn begins accepting requests.

3. Access the running services

| Resource   | URL                                  |
| ---------- | ------------------------------------ |
| API base   | `http://localhost:8000/api/v1`       |
| Swagger UI | `http://localhost:8000/api/v1/docs`  |
| ReDoc      | `http://localhost:8000/api/v1/redoc` |
| PostgreSQL | `localhost:5432`                     |

4. Stop and clean up

```bash
docker compose down      # stop containers, keep data volume
docker compose down -v   # stop containers and delete the database volume
```

---

## 🔌 API reference

Base path: `/api/v1`

### Endpoints

| Method   | Path                 | Auth  | Description                                  |
| -------- | -------------------- | :---: | -------------------------------------------- |
| `POST`   | `/auth/register`     |   —   | Register a new user                          |
| `POST`   | `/auth/token`        |   —   | Login and receive a JWT access token         |
| `GET`    | `/users/me`          |   🔒   | Get current user profile                     |
| `PATCH`  | `/users/me`          |   🔒   | Update current user profile                  |
| `PATCH`  | `/users/me/password` |   🔒   | Change current user password                 |
| `GET`    | `/items/`            |   🔒   | List authenticated user's items (paginated)  |
| `POST`   | `/items/`            |   🔒   | Create a new item                            |
| `GET`    | `/items/{id}`        |   🔒   | Get one of the authenticated user's items    |
| `PATCH`  | `/items/{id}`        |   🔒   | Update one of the authenticated user's items |
| `DELETE` | `/items/{id}`        |   🔒   | Delete one of the authenticated user's items |
| `POST`   | `/items/import`      |   🔒   | Import an item from a validated external URL |
| `GET`    | `/admin/users`       |   👑   | List all users                               |
| `PATCH`  | `/admin/users/{id}`  |   👑   | Update any user                              |
| `GET`    | `/admin/items`       |   👑   | List all items                               |

> 🔒 Bearer token required &nbsp;·&nbsp; 👑 Admin role required

### Example workflow

**1. Login and capture the token**

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=ChangeMe@1" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**2. Create an item**

```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My first item", "description": "Hello world", "price": 9.99}'
```

**3. List your items**

```bash
curl "http://localhost:8000/api/v1/items/?page=1&size=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Testing

The test suite covers three layers — unit, integration, and full API.

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing
```

---

## 🔬 Code quality

Install pre-commit hooks once after cloning:

```bash
uv run pre-commit install
```

Run checks manually at any time:

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy                  # type check
uv run pre-commit run --all-files   # all hooks
```

Hooks run automatically on every `git commit` in the order: Ruff lint → Ruff format → Mypy.

---

## 🛡️ Security

**This project is a learning resource, not a production template.** Feel free to study it, fork it, and experiment with it — but always review and adapt it before using any part of it in a real application.

**Found a bug or vulnerability in this repo?**
Please do not report it in a public GitHub issue. Instead, use the private [GitHub Security Advisory](https://github.com/mouakos/fastapi-owasp-api-security-top10/security/advisories/new) form or reach out directly via [GitHub](https://github.com/mouakos). This keeps the details private until a fix is ready.

---

## 📚 Further reading

Resources used as reference for this project:

- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) — the authoritative list this project is based on
- [OWASP API Security Project](https://owasp.org/www-project-api-security/) — cheat sheets, testing guides, and tooling
- [FastAPI Security docs](https://fastapi.tiangolo.com/tutorial/security/) — official FastAPI security patterns
- [PyJWT documentation](https://pyjwt.readthedocs.io/) — JWT token handling
- [Argon2 password hashing](https://argon2-cffi.readthedocs.io/) — the recommended password hashing algorithm
- [SlowAPI rate limiting](https://slowapi.readthedocs.io/) — rate limiting for ASGI apps

---

## 🤝 Contributing

Contributions are welcome.

- [Open an issue](https://github.com/mouakos/fastapi-owasp-api-security-top10/issues) for bugs or feature requests
- [Start a discussion](https://github.com/mouakos/fastapi-owasp-api-security-top10/discussions) for feedback or questions
- Submit a pull request with focused, tested changes

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

<div align="center">

Built by [Stephane Mouako](https://github.com/mouakos)

</div>

