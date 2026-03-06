"""
Unit tests for the authentication module.

Tests password hashing, session management, and CSRF protection.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from api import auth  # noqa: E402


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_produces_salt_and_hash(self):
        result = auth._hash_password("test123")
        assert ":" in result
        salt, h = result.split(":", 1)
        assert len(salt) == 32  # 16 bytes hex
        assert len(h) == 64  # sha256 hex

    def test_verify_correct_password(self):
        stored = auth._hash_password("mypassword")
        assert auth._verify_password("mypassword", stored) is True

    def test_verify_wrong_password(self):
        stored = auth._hash_password("mypassword")
        assert auth._verify_password("wrongpassword", stored) is False

    def test_verify_empty_password(self):
        stored = auth._hash_password("mypassword")
        assert auth._verify_password("", stored) is False

    def test_verify_malformed_hash(self):
        assert auth._verify_password("test", "nocolon") is False

    def test_different_hashes_for_same_password(self):
        hash1 = auth._hash_password("same")
        hash2 = auth._hash_password("same")
        # Different salts produce different hashes
        assert hash1 != hash2
        # But both verify correctly
        assert auth._verify_password("same", hash1) is True
        assert auth._verify_password("same", hash2) is True


class TestAuthEnabled:
    """Tests for auth_enabled check."""

    def test_auth_disabled_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(auth, "PASSWORD_FILE", str(tmp_path / "missing"))
        assert auth.auth_enabled() is False

    def test_auth_enabled_when_file_exists(self, tmp_path, monkeypatch):
        pw_file = tmp_path / ".admin_password"
        pw_file.write_text(auth._hash_password("test"))
        monkeypatch.setattr(auth, "PASSWORD_FILE", str(pw_file))
        assert auth.auth_enabled() is True


class TestCSRFToken:
    """Tests for CSRF token generation and validation."""

    def test_generate_csrf_token(self, tmp_path, monkeypatch):
        from dev_server import app

        monkeypatch.setattr(auth, "PASSWORD_FILE", str(tmp_path / "missing"))
        with app.test_request_context():

            token = auth.generate_csrf_token()
            assert len(token) == 64  # 32 bytes hex
            # Same call returns same token
            assert auth.generate_csrf_token() == token

    def test_csrf_validation_passes_when_auth_disabled(self, tmp_path, monkeypatch):
        from dev_server import app

        monkeypatch.setattr(auth, "PASSWORD_FILE", str(tmp_path / "missing"))
        with app.test_request_context():
            assert auth.validate_csrf_token() is True
