"""
Authentication module for the web configuration panel.

Provides optional password protection for write endpoints.
When no password file exists, authentication is disabled (open access).
"""

import functools
import hashlib
import logging
import os
import secrets
import time

from flask import Blueprint, redirect, render_template, request, session, url_for

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "..", ".admin_password")

# Session timeout: 30 minutes of inactivity
SESSION_TIMEOUT = 1800


def _read_password_hash():
    """Read the stored password hash, or return None if auth is disabled."""
    path = os.path.normpath(PASSWORD_FILE)
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _hash_password(password):
    """Hash a password using SHA-256 with salt."""
    # Format: salt:hash
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password, stored):
    """Verify a password against a stored salt:hash."""
    if ":" not in stored:
        return False
    salt, expected_hash = stored.split(":", 1)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return secrets.compare_digest(h, expected_hash)


def auth_enabled():
    """Check whether authentication is configured."""
    return _read_password_hash() is not None


def is_authenticated():
    """Check if the current session is authenticated."""
    if not auth_enabled():
        return True

    if "authenticated" not in session:
        return False

    # Check session timeout
    last_activity = session.get("last_activity", 0)
    if time.time() - last_activity > SESSION_TIMEOUT:
        session.clear()
        return False

    # Refresh activity timestamp
    session["last_activity"] = time.time()
    return True


def login_required(f):
    """Decorator to require authentication on write endpoints."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return {"error": "Authentication required"}, 401
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated


def generate_csrf_token():
    """Generate or retrieve a CSRF token for the current session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token():
    """Validate the CSRF token from a request. Returns True if valid."""
    if not auth_enabled():
        return True

    token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    expected = session.get("csrf_token")
    if not token or not expected:
        return False
    return secrets.compare_digest(token, expected)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page and form handler."""
    if not auth_enabled():
        return redirect("/settings")

    if request.method == "GET":
        next_url = request.args.get("next", "/settings")
        return render_template("login.html", next=next_url, error=None)

    password = request.form.get("password", "")
    next_url = request.form.get("next", "/settings")

    stored_hash = _read_password_hash()
    if stored_hash and _verify_password(password, stored_hash):
        session["authenticated"] = True
        session["last_activity"] = time.time()
        session["csrf_token"] = secrets.token_hex(32)
        logger.info("Admin login successful")
        return redirect(next_url)

    logger.warning("Failed login attempt")
    return render_template("login.html", next=next_url, error="Incorrect password"), 401


@auth_bp.route("/logout")
def logout():
    """Clear session and redirect to display."""
    session.clear()
    return redirect("/")
