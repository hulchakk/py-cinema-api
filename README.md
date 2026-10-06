# Movie Store API

Backend REST API for video-on-demand and movie purchasing.

Handles user accounts, movie catalogs, shopping carts, orders, and Stripe payments through a single unified platform.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Web framework with async/await and automatic OpenAPI docs |
| **PostgreSQL + SQLAlchemy** | Async ORM for data persistence |
| **Celery + Redis** | Background job queue for emails and scheduled tasks |
| **Stripe API** | Payment processing and webhook handling |
| **S3 (MinIO)** | Object storage for user avatars and media |
| **Docker Compose** | Local development environment |

## Getting Started

```bash
# Start local environment (app, database, Redis, S3, email)
docker-compose -f docker/docker-compose.local.yaml up --build

# Run tests
docker-compose -f docker/docker-compose.test.yaml up --build
```

API docs available at `http://localhost:8000/docs` once running.

## Key Decisions

**Dependency Injection:** FastAPI's `Depends` system with interface abstractions (`JWTAuthManagerInterface`, `EmailSenderInterface`, `S3StorageInterface`) — loose coupling, testable, swappable implementations.

**JWT + Role-Based Access Control:** OAuth2 bearer tokens validated on each request; `PermissionChecker` dependency gates endpoints by user group (Admin, Moderator, User).

**Async Background Tasks:** Long-running work (email, webhook processing) handled by Celery workers so HTTP responses stay fast.

**Stripe Webhooks:** Webhook listeners update order status asynchronously in response to payment events — source of truth is Stripe.

## Features

- User registration, email verification, login, token refresh, password recovery
- Movie catalog with advanced filtering (year, price, rating, duration, genres, directors)
- Shopping cart and checkout via Stripe
- Order and payment history
- User profiles with avatar uploads (S3)
- Admin CRUD for catalog management

## Status

Fully functional. All core endpoints tested and documented in Swagger UI.
