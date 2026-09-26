

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
        # REST should return JSON:API format
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "meta" in data
        assert "timestamp" in data["meta"]
