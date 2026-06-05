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
