# gflask

A reusable authentication and utility library for Flask applications.

gflask provides a plug-and-play authentication system (Login, Signup, Password Reset, Verification) along with a suite of very basic utilities for database management, form validation, and email handling.

## Installation

Since this is a local package, you can install it in editable mode within your project:

```bash
pip install -e .
```

## Quick Start

To integrate gflask into your Flask application, you only need to initialize the `GFlaskAuth` extension.

### 1. Basic Setup
In your `app.py` or application factory:

```python
from flask import Flask
from gflask import GFlaskAuth

app = Flask(__name__)

# Required Configurations
app.config["SECRET_KEY"] = "your-very-secret-key"
app.config["DATABASE_URL"] = "sqlite:///your_database.db"
app.config["APP_NAME"] = "My New Project"

# Initialize GFlaskAuth
auth = GFlaskAuth(app)
```

### 2. Protecting Routes
The library integrates with **Flask-Login**. You can use the standard decorators to protect your application's routes:

```python
from flask_login import login_required, current_user

@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome to your dashboard, {current_user.name}!"
```

## Available Modules

gflask exposes its core utilities directly at the package level for easy access:

- **`db`**: A centralized SQLAlchemy-based database manager for executing raw SQL (Query, Insert, Execute) within or outside transactions.
- **`utils`**: Helpers for token generation, date formatting, and string manipulation.
- **`validate`**: A `Validator` class for checking form inputs (email, password strength, strings, etc.).
- **`mail`**: A simplified interface for sending emails via SMTP, SendGrid, or Gmail.
- **`Counter`**: An atomic database-backed counter for tracking events or visits.
- **`User`**: The standard user model compatible with Flask-Login.

Example usage:
```python
from gflask import db, utils, validate

# Generate a unique token
token = utils.get_token()

# Validate a form
v = validate.Validator(request.form)
email = v.check("email", "email")
```

## Localization

The library has built-in support for **Flask-Babel** and is pre-translated in **English** and **Italian**. It automatically handles language selection based on the user's profile settings or browser preferences.

## UI Customization

gflask uses **Pico.css** for a clean, responsive default look. You can override any library template by creating a file with the same name in your project's `templates/` folder:

- `login.html`, `signup.html`, `forgot.html`, `reset.html`, `verify.html`, `settings.html`, `profile.html`.