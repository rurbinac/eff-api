import pytest
from datetime import datetime
from app.models import User
from app.context import RequestContext
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction, SignUpAction, UpdateUserAction
from app.security import hash_password


class TestSignInAction:
    """Tests for SignInAction."""

    def test_signin_success(self, test_db, test_user):
        """Test successful sign in."""
        RequestContext.set_datetime()
        try:
            result = SignInAction.execute(
                test_db,
                user_email=test_user.userEmail,
                user_password="password123",
                client_ip="127.0.0.1"
            )

            assert isinstance(result, dict)
            assert result["userID"] == test_user.userID
            assert result["userEmail"] == test_user.userEmail
            assert "token" in result
            assert result["feedsMode"] == 0
        finally:
            RequestContext.reset()

    def test_signin_invalid_email(self, test_db):
        """Test sign in with invalid email."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                SignInAction.execute(
                    test_db,
                    user_email="nonexistent@example.com",
                    user_password="password",
                    client_ip="127.0.0.1"
                )
        finally:
            RequestContext.reset()

    def test_signin_wrong_password(self, test_db, test_user):
        """Test sign in with wrong password."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                SignInAction.execute(
                    test_db,
                    user_email=test_user.userEmail,
                    user_password="WRONG_PASSWORD",
                    client_ip="127.0.0.1"
                )
        finally:
            RequestContext.reset()


class TestSignOutAction:
    """Tests for SignOutAction."""

    def test_signout_success(self):
        """Test sign out."""
        result = SignOutAction.execute(1)

        assert isinstance(result, dict)
        assert result["success"] is True


class TestSignInfoAction:
    """Tests for SignInfoAction."""

    def test_signinfo_success(self, test_db, test_user):
        """Test successful SignInfo."""
        RequestContext.set_datetime()
        try:
            result = SignInfoAction.execute(test_db, test_user.userID)

            assert isinstance(result, dict)
            assert result["userID"] == test_user.userID
            assert "token" not in result  # No token in SignInfo response
        finally:
            RequestContext.reset()

    def test_signinfo_invalid_user(self, test_db):
        """Test SignInfo with invalid user ID."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                SignInfoAction.execute(test_db, 99999)
        finally:
            RequestContext.reset()


class TestSignUpAction:
    """Tests for SignUpAction."""

    def test_signup_success(self, test_db, test_lookups):
        """Test successful sign up."""
        RequestContext.set_datetime()
        try:
            result = SignUpAction.execute(
                test_db,
                user_email="newuser@example.com",
                user_password="newpassword123",
                user_name="newuser",
                first_name="New",
                last_name="User",
                birthday=datetime(1990, 1, 15),
                country="US",
                state="CA"
            )

            assert isinstance(result, dict)
            assert result["userEmail"] == "newuser@example.com"
            assert result["userName"] == "newuser"
            assert "token" in result
        finally:
            RequestContext.reset()

    def test_signup_duplicate_email(self, test_db, test_user):
        """Test sign up with existing email."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                SignUpAction.execute(
                    test_db,
                    user_email=test_user.userEmail,
                    user_password="password",
                    user_name="user2",
                    first_name="Another",
                    last_name="User",
                    birthday=datetime(1990, 1, 15)
                )
        finally:
            RequestContext.reset()


class TestUpdateUserAction:
    """Tests for UpdateUserAction."""

    def test_update_user_success(self, test_db, test_user, test_lookups):
        """Test successful user update."""
        RequestContext.set_datetime()
        try:
            result = UpdateUserAction.execute(
                test_db,
                user_id=test_user.userID,
                first_name="Updated",
                last_name="Name",
                country="GB",
                city="London"
            )

            assert isinstance(result, dict)
            assert result["firstName"] == "Updated"
            assert result["lastName"] == "Name"
            assert result["country"] == "GB"
            assert result["city"] == "London"
        finally:
            RequestContext.reset()

    def test_update_user_invalid_id(self, test_db):
        """Test update with invalid user ID."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                UpdateUserAction.execute(
                    test_db,
                    user_id=99999,
                    first_name="Test"
                )
        finally:
            RequestContext.reset()
