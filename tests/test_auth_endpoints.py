import pytest
from datetime import datetime


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_rest_signin(self, test_client, test_user):
        """Test REST SignIn endpoint."""
        response = test_client.post(
            "/api/auth/signin",
            json={
                "userEmail": test_user.userEmail,
                "userPassword": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["userID"] == test_user.userID
        assert "token" in data
        assert data["feedsMode"] == 0

    def test_rest_signin_invalid(self, test_client):
        """Test REST SignIn with invalid credentials."""
        response = test_client.post(
            "/api/auth/signin",
            json={
                "userEmail": "invalid@example.com",
                "userPassword": "wrong"
            }
        )

        assert response.status_code == 401

    def test_rest_signup(self, test_client, test_lookups):
        """Test REST SignUp endpoint."""
        response = test_client.post(
            "/api/auth/signup",
            json={
                "userEmail": "newuser@example.com",
                "userPassword": "password123",
                "userName": "newuser",
                "firstName": "New",
                "lastName": "User",
                "birthday": "1990-01-15",
                "country": "US",
                "state": "CA"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["userEmail"] == "newuser@example.com"
        assert "token" in data

    def test_rest_signup_duplicate_email(self, test_client, test_user):
        """Test SignUp with duplicate email."""
        response = test_client.post(
            "/api/auth/signup",
            json={
                "userEmail": test_user.userEmail,
                "userPassword": "password",
                "userName": "user2",
                "firstName": "Another",
                "lastName": "User"
            }
        )

        assert response.status_code == 400

    def test_rest_signout(self, test_client):
        """Test REST SignOut endpoint."""
        response = test_client.post("/api/auth/signout")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_rest_update_user(self, test_client, test_user, test_lookups):
        """Test REST UpdateUser endpoint."""
        response = test_client.patch(
            f"/api/auth/users/{test_user.userID}",
            json={
                "firstName": "Updated",
                "lastName": "Name",
                "country": "GB",
                "city": "London"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["firstName"] == "Updated"
        assert data["lastName"] == "Name"
        assert data["country"] == "GB"
        assert data["city"] == "London"

    def test_legacy_signin(self, test_client, test_user):
        """Test Legacy SignIn endpoint."""
        response = test_client.post(
            "/eff/eff_api/Users.php?f=SignIn",
            data={
                "_format": "json",
                "userEmail": test_user.userEmail,
                "userPassword": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Session"
        assert "timestamp" in data
        assert data["values"]["userID"] == test_user.userID
        assert "token" in data["values"]

    def test_legacy_signout(self, test_client):
        """Test Legacy SignOut endpoint."""
        response = test_client.post(
            "/eff/eff_api/SignOut.php",
            data={"_format": "json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "success"
        assert data["values"]["success"] is True
