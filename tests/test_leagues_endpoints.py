import pytest


class TestLeaguesEndpoints:
    """Tests for leagues endpoints."""

    def test_legacy_leagues_readlist(self, test_client, test_user):
        """Test Legacy Leagues ReadList endpoint."""
        response = test_client.post(
            "/eff/eff_api/Leagues.php?f=ReadList",
            data={
                "_format": "json",
                "_type": "byUserID",
                "userID": test_user.userID
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Leagues"
        assert "timestamp" in data
        assert isinstance(data["items"], list)
        # Items should be wrapped in {"values": {...}}
        if data["items"]:
            assert "values" in data["items"][0]

    def test_rest_leagues_readlist(self, test_client, test_user):
        """Test REST Leagues ReadList endpoint."""
        response = test_client.post(
            "/api/leagues/readlist",
            json={"userID": test_user.userID}
        )

        assert response.status_code == 200
        data = response.json()
        # REST should return direct array
        assert isinstance(data, list)

    def test_gaming_api_league_build(self, test_client, test_user, test_db, test_lookups):
        """Test Gaming API League Build endpoint."""
        # First get a token
        signin_response = test_client.post(
            "/api/auth/signin",
            json={
                "userEmail": test_user.userEmail,
                "userPassword": "password123"
            }
        )
        token = signin_response.json()["token"]

        # Build a league
        response = test_client.post(
            "/gaming/api/Leagues.php?f=Build",
            data={
                "_format": "json",
                "leagueName": "Test League",
                "leaguePassword": "testpass",
                "leagueType": "1",
                "gameType": "2",
                "scoringSystem": "1",
                "tradeDeadline": "2026-06-15 14:00:00",
                "publishLeague": "1",
                "seasonStatus": "1",
                "teamsPerDivision": "8,10"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Leagues"
        assert "timestamp" in data
        assert data["values"]["leagueName"] == "Test League"
        assert data["values"]["numDivisions"] == 2
        assert data["values"]["totalTeams"] == 18

    def test_gaming_api_league_join(self, test_client, test_user, test_db, test_lookups):
        """Test Gaming API League Join endpoint."""
        # First create a league
        signin_response = test_client.post(
            "/api/auth/signin",
            json={
                "userEmail": test_user.userEmail,
                "userPassword": "password123"
            }
        )
        token = signin_response.json()["token"]

        build_response = test_client.post(
            "/gaming/api/Leagues.php?f=Build",
            data={
                "_format": "json",
                "leagueName": "Join Test League",
                "leaguePassword": "joinpass",
                "leagueType": "1",
                "gameType": "2",
                "scoringSystem": "1",
                "tradeDeadline": "2026-06-15 14:00:00",
                "publishLeague": "1",
                "seasonStatus": "1",
                "teamsPerDivision": "8,10"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        league_id = build_response.json()["values"]["leagueID"]
        league_password = "joinpass"

        # Join the league
        response = test_client.post(
            "/gaming/api/Leagues.php?f=Join",
            data={
                "_format": "json",
                "leagueID": str(league_id),
                "leaguePassword": league_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Teams"
        assert "timestamp" in data
        assert data["values"]["leagueID"] == league_id
        assert data["values"]["userID"] == test_user.userID

    def test_gaming_api_league_join_invalid_password(self, test_client, test_user, test_lookups):
        """Test League Join with wrong password."""
        signin_response = test_client.post(
            "/api/auth/signin",
            json={
                "userEmail": test_user.userEmail,
                "userPassword": "password123"
            }
        )
        token = signin_response.json()["token"]

        response = test_client.post(
            "/gaming/api/Leagues.php?f=Join",
            data={
                "_format": "json",
                "leagueID": "1",
                "leaguePassword": "wrongpass"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
