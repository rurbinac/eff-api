import pytest


class TestLookupsEndpoints:
    """Tests for lookups endpoints."""

    def test_legacy_lookups_readlist(self, test_client):
        """Test Legacy Lookups ReadList endpoint."""
        response = test_client.post(
            "/eff/eff_api/Lookups.php?f=ReadList",
            data={
                "_format": "json",
                "lookupType": "1"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "Lookups"
        assert "timestamp" in data
        assert isinstance(data["items"], list)
        # Items should be sorted by position ASC
        if len(data["items"]) > 1:
            positions = [item["values"]["position"] for item in data["items"]]
            assert positions == sorted(positions)

    def test_rest_lookups_readlist(self, test_client):
        """Test REST Lookups ReadList endpoint."""
        response = test_client.post(
            "/api/lookups/readlist",
            json={"lookupType": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "meta" in data
        assert "timestamp" in data["meta"]
        # Should be sorted by position
        if len(data["data"]) > 1:
            positions = [item["attributes"]["position"] for item in data["data"]]
            assert positions == sorted(positions)

    def test_lookups_readlist_country(self, test_client):
        """Test reading country lookups."""
        response = test_client.post(
            "/api/lookups/readlist",
            json={"lookupType": 1}  # COUNTRY_CODE = 1
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        # Verify structure of lookup items
        for item in data["data"]:
            assert "type" in item
            assert "id" in item
            assert "attributes" in item
            assert "lookupID" in item["attributes"]
            assert "lookupType" in item["attributes"]
            assert "position" in item["attributes"]
