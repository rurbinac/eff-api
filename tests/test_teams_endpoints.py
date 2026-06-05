import pytest


class TestTeamsEndpoints:
    """Tests for teams endpoints."""

    def test_legacy_teams_readlist_by_league(self, test_client):
        """Test Legacy Teams ReadList endpoint by league."""
        response = test_client.post(
            "/eff/eff_api/Teams.php?f=ReadList",
            data={
                "_format": "json",
                "_type": "byLeagueID",
                "leagueID": "1"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Teams"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_legacy_teams_readlist_by_division(self, test_client):
        """Test Legacy Teams ReadList endpoint by division."""
        response = test_client.post(
            "/eff/eff_api/Teams.php?f=ReadList",
            data={
                "_format": "json",
                "_type": "byDivisionID",
                "divisionID": "1"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Teams"
        assert isinstance(data["items"], list)

    def test_rest_teams_readlist(self, test_client):
        """Test REST Teams ReadList endpoint."""
        response = test_client.post(
            "/api/teams/readlist",
            json={"leagueID": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_legacy_teams_get_real_members_ranking(self, test_client):
        """Test Legacy Teams GetRealMembersRanking endpoint."""
        response = test_client.post(
            "/eff/eff_api/Teams.php?f=GetRealMembersRanking",
            data={
                "_format": "json",
                "teamID": "1"
            }
        )

        # Should return 200 even if no data
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "RealTeamMembers"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_rest_teams_get_real_members_ranking(self, test_client):
        """Test REST Teams GetRealMembersRanking endpoint."""
        response = test_client.post(
            "/api/teams/real-members-ranking",
            json={"teamID": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_gaming_api_teams_get_current_members(self, test_client):
        """Test Gaming API Teams GetCurrentMembers endpoint."""
        response = test_client.post(
            "/gaming/api/Teams.php?f=GetCurrentMembers",
            data={
                "_format": "json",
                "teamID": "1"
            }
        )

        # Should return 200 even if no members
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "RealTeamMembers"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_gaming_api_teams_set_real_members_ranking(self, test_client, test_user):
        """Test Gaming API Teams SetRealMembersRanking endpoint."""
        from app.security import create_access_token

        # Create a test token
        token = create_access_token({"sub": str(test_user.userID), "email": test_user.userEmail})

        response = test_client.post(
            "/gaming/api/Teams.php?f=SetRealMembersRanking",
            data={
                "_format": "json",
                "teamID": "1",
                "memberKeys": "P1,T2,P3"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail with 400 because team 1 doesn't exist or user doesn't own it
        # But the endpoint should be callable and handle auth properly
        assert response.status_code in (200, 400)
        data = response.json()
        assert isinstance(data, dict)
