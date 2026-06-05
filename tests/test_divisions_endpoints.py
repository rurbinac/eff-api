import pytest


class TestDivisionsEndpoints:
    """Tests for divisions endpoints."""

    def test_legacy_divisions_readlist(self, test_client):
        """Test Legacy Divisions ReadList endpoint."""
        response = test_client.post(
            "/eff/eff_api/Divisions.php?f=ReadList",
            data={
                "_format": "json",
                "leagueID": "1"
            }
        )

        # Should return 200 even if no divisions exist
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Divisions"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_rest_divisions_readlist(self, test_client):
        """Test REST Divisions ReadList endpoint."""
        response = test_client.post(
            "/api/divisions/readlist",
            json={"leagueID": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_legacy_divisions_transactions_detail(self, test_client):
        """Test Legacy Divisions TransactionsDetail endpoint."""
        response = test_client.post(
            "/eff/eff_api/Divisions.php?f=TransactionsDetail",
            data={
                "_format": "json",
                "divisionID": "1"
            }
        )

        # Should return 200 even if no data (empty result is valid)
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "TransactionsDetail"
        assert "timestamp" in data
        assert isinstance(data["items"], list)

    def test_rest_divisions_transactions_detail(self, test_client):
        """Test REST Divisions TransactionsDetail endpoint."""
        response = test_client.post(
            "/api/divisions/transactions-detail",
            json={"divisionID": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
