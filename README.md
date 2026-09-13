# Movie Store API

A robust backend REST API built with Python and FastAPI for a video-on-demand and movie purchasing platform. This project serves as a portfolio piece to demonstrate modern backend development practices, clean architecture, and the integration of various internal and external services.

## Tech Stack

* **Framework:** Python, FastAPI
* **Database:** PostgreSQL, SQLAlchemy (Async)
* **Background Tasks:** Celery, Celery-beat, Redis
* **Storage:** S3 (MinIO)
* **Payments:** Stripe API
* **Email:** SMTP (Mailhog for local testing)
* **Infrastructure:** Docker, Docker Compose

## Highlighted Skills and Architecture

This project was built with a focus on maintainability, scalability, and best practices. Key technical achievements include:

* **Dependency Inversion Principle (DIP):** Extensive use of FastAPI's dependency injection system (`Depends`). Business logic depends on abstractions and interfaces (e.g., `JWTAuthManagerInterface`, `EmailSenderInterface`, `S3StorageInterface`) rather than concrete implementations, making the codebase highly testable and decoupled.
* **Authentication & Authorization:** Implemented robust JWT authentication integrated with `OAuth2PasswordBearer`. This allows developers to interactively test protected endpoints directly through the Swagger UI.
* **Role-Based Access Control (RBAC):** Created a scalable `PermissionChecker` dependency to manage endpoint access based on user groups (e.g., Admin, Moderator, User).
* **Asynchronous Background Processing:** Offloaded heavy tasks such as SMTP email notifications (account activation, password resets, order confirmations) to background workers using Celery and Celery-beat with a Redis message broker.
* **S3 Cloud Storage:** Demonstrated handling of multipart form data and external object storage integration by implementing an avatar upload endpoint that communicates with an S3-compatible bucket (MinIO).
* **Third-Party Payment Integration:** Securely implemented Stripe checkout sessions and configured Stripe webhook listeners to handle asynchronous payment success events and update database order statuses.
* **Pagination & Configuration:** Leveraged `pydantic-settings` for robust environment variable validation and configuration management. Implemented standardized pagination across all list endpoints (movies, catalogs, libraries, orders).
* **Comprehensive API Documentation:** All endpoints are heavily documented using OpenAPI/Swagger standards, including detailed request schemas, response models, query parameter validation, and explicit error code definitions.

## Core Domain Features

* **User Accounts:** Registration, email verification, login, JWT token refresh, and password recovery.
* **Profiles:** User profile management, avatar uploads (via S3), and a private library of purchased movies.
* **Movie Catalog:** Advanced filtering and search endpoints for movies (by year, price, IMDb rating, duration, genres, directors, and stars). Admins have full CRUD access to the catalog.
* **Shopping Cart & Checkout:** Cart item management, order creation, and Stripe checkout session generation.
* **Order & Payment Lifecycle:** Automated order status updates triggered by Stripe webhooks and comprehensive payment history tracking.

## Local Development and Setup

The project is fully dockerized to ensure a consistent environment across development and testing. The setup includes the application backend, PostgreSQL, Redis, MinIO (S3), and Mailhog (for catching SMTP emails locally).

All Docker configurations are located in the `docker` directory.

**To run the application locally:**

```bash
docker-compose -f docker/docker-compose.local.yaml up --build

```

**To run the automated test suite:**

```bash
docker-compose -f docker/docker-compose.test.yaml up --build

```

Once the local container is running, the interactive Swagger API documentation will be available at `/docs`, allowing you to log in, receive a JWT, and test the endpoints directly from your browser.
