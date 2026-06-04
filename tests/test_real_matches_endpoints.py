import pytest


class TestRealMatchesEndpoints:
    """Tests for real matches endpoints."""

    def test_legacy_real_matches_readlist(self, test_client):
        """Test Legacy RealMatches ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            # Get season and real competition IDs for current date
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/eff/eff_api/RealMatches.php?f=ReadList",
                data={
                    "_format": "json",
                    "realCompetitionID": "3",  # EPL
                    "realCompetitionSeasonID": str(season_id)
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "RealMatches"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_real_matches_readlist(self, test_client):
        """Test REST RealMatches ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/api/realmatches/readlist",
                json={
                    "realCompetitionID": 3,
                    "realCompetitionSeasonID": season_id
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            RequestContext.reset()

    def test_real_matches_readlist_filters(self, test_client):
        """Test RealMatches with multiple filter combinations."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            # Test with different competition IDs if available
            for comp_id in [1, 2, 3]:  # Different competitions
                response = test_client.post(
                    "/api/realmatches/readlist",
                    json={
                        "realCompetitionID": comp_id,
                        "realCompetitionSeasonID": season_id
                    }
                )

                # Should return 200 regardless of whether data exists
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            RequestContext.reset()
