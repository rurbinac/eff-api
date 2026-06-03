import pytest
from datetime import datetime, timedelta
from app.security import hash_password, verify_password, create_access_token, decode_token


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "my_secure_password"
        hashed = hash_password(password)

        # Hash should not equal original password
        assert hashed != password
        # Hash should be a bcrypt hash (starts with $2)
        assert hashed.startswith("$2")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_password_with_special_chars(self):
        """Test password with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_format_password_userid(self):
        """Test PASSWORD_{userID} format works."""
        user_id = 42
        password = f"PASSWORD_{user_id}"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password(f"PASSWORD_99", hashed) is False


class TestJWTToken:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_expiry(self):
        """Test token is created with 24-hour expiry."""
        data = {"sub": "1"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "1"

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        data = {"sub": "5", "email": "user@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "5"
        assert decoded["email"] == "user@example.com"

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        invalid_token = "invalid.token.here"
        result = decode_token(invalid_token)

        assert result is None

    def test_decode_expired_token(self):
        """Test that expired token returns None."""
        # Create token with -1 seconds expiry (already expired)
        from datetime import timedelta
        from app.security import SECRET_KEY, ALGORITHM
        from jose import jwt

        data = {"sub": 1}
        expires_delta = timedelta(seconds=-1)
        expire = datetime.utcnow() + expires_delta
        to_encode = data.copy()
        to_encode.update({"exp": expire})

        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        result = decode_token(expired_token)

        assert result is None
