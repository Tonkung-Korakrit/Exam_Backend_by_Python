"# Exam_Backend_by_Python" 
# E-Commerce REST API

A robust backend REST API for an E-commerce platform, built with Django REST Framework (DRF). This system supports role-based access control (Buyers and Sellers), product management, shopping cart operations, and a secure checkout process with atomic database transactions.

## Architectural Choices

* **Framework:** **Django REST Framework (DRF)** for rapid development, robust serialization, and seamless Django ORM integration.
* **Database:** **PostgreSQL** (via Docker) ensures a consistent environment and handles relational data efficiently, replacing SQLite for production readiness.
* **Authentication:** **SimpleJWT (JSON Web Tokens)** provides stateless authentication, decoupling the backend from the frontend.
* **Security & Configuration:** Environment variables (`python-dotenv`) are used to secure sensitive data like `SECRET_KEY` and database credentials.
* **Role-Based Access Control (RBAC):** Custom permissions restrict actions based on user roles (`SELLER` for inventory, `BUYER` for checkout).
* **Data Integrity:** **Database Transactions (`transaction.atomic`)** ensure that inventory deductions and order creations either succeed entirely or roll back completely.

---

## Environment Variables (.env)

Create a `.env` file in the root directory (same level as `manage.py`) and configure the following variables before running the project. **Do not commit this file to version control.**

```env
SECRET_KEY=your_django_secret_key_here
DEBUG=True

# PostgreSQL Database Configurations
POSTGRES_DB=ecom_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
```

---

# Setup Instructions

Follow these steps to set up the development environment locally.

## 1. Database Setup (Docker)
Start the PostgreSQL database using Docker Compose:

```bash
docker-compose up -d
```

(To stop and remove database volumes later: docker-compose down -v)

## 2. Virtual Environment & Dependencies
Create and activate your virtual environment to avoid dependency conflicts (Dependency Hell):

```bash
python -m venv venv
```

### On Windows:
```bash
venv\Scripts\activate
```
### On Mac/Linux:
```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

(Note: Includes python-dotenv for config management and Pillow for image validation).

## 3. Database Migrations
Generate and apply database tables from the Django models:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 4. Create Admin User
Create a superuser account to access the Django Admin panel (Email can be left blank):

```bash
python manage.py createsuperuser
```

## 5. Run the Server
Start the local development server:

```bash
python manage.py runserver
```

---

# API Endpoints Reference

## Authentication

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/register/` | Register a new user | `username`, `password`, `email`, `role` ("SELLER" or "BUYER") |
| `POST` | `/api/auth/login/` | Login and get JWT Token | `username`, `password` |

## API Endpoints Reference

| Method | Endpoint | Description | Payload / Query Parameters |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/register/` | Register a new user | `username, password, email, role ("SELLER" or "BUYER")` | Create a product (Seller only) | `title, description, unit_price, available_quantity`
| `POST` | `/api/auth/login/` | Login and get JWT Token | `username, password` |

## Products (Catalog & Management)

| Method | Endpoint | Description | Payload / Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products/` | List all products | `Supports search & filters`
| `POST` | `/api/auth/login/` | Login and get JWT Token | `username, password` |
| `POST` | `/api/products/` | List all products | `Supports search & filters`
| `POST` | `/api/auth/login/` | Create a product (Seller only) | `title, description, unit_price, available_quantity` |

## Search & Filter Examples:
- Search by word or seller name: ?search=YONEX or ?search=tonkung
- Filter by price range: ?min_price=1000&max_price=3000
- Ordering: ?ordering=unit_price (Ascending) or ?ordering=-unit_price (Descending)
- Combined Filters: ?search=ไม้แบด&max_price=2000&ordering=unit_price

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/cart/` | Add item to cart | `product_id, quantity` |
| `POST` | `/api/cart/payment/` | Checkout and deduct stock | `None (Reads items automatically from Cart)`

## Unit Testing
To ensure the core business logic remains stable (including role access and atomic inventory updates), run the test suite:

```bash
python manage.py test api
```