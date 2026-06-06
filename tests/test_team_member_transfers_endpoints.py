import pytest


class TestTeamMemberTransfersEndpoints:
    """Tests for TeamMemberTransfers endpoints."""

    def test_legacy_team_member_transfers_get_pending_by_team_id(self, test_client):
        """Test Legacy TeamMemberTransfers GetPendingByTeamID endpoint."""
        response = test_client.post(
            "/eff/eff_api/TeamMemberTransfers.php?f=GetPendingByTeamID",
            data={
                "_format": "json",
                "teamID": "1"
            }
        )

        # Should return 200 even if no data
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "TeamMemberTransfers"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_legacy_team_member_transfers_missing_team_id(self, test_client):
        """Test Legacy TeamMemberTransfers endpoint with missing teamID."""
        response = test_client.post(
            "/eff/eff_api/TeamMemberTransfers.php?f=GetPendingByTeamID",
            data={"_format": "json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_rest_team_member_transfers_get_pending(self, test_client):
        """Test REST TeamMemberTransfers pending endpoint."""
        response = test_client.post(
            "/api/team-member-transfers/pending",
            json={"teamID": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_rest_team_member_transfers_missing_team_id(self, test_client):
        """Test REST TeamMemberTransfers endpoint with missing teamID."""
        response = test_client.post(
            "/api/team-member-transfers/pending",
            json={}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
