import pytest


class TestDivisionsEndpoints:
    """Tests for divisions endpoints."""

    def test_legacy_divisions_readlist(self, test_client, test_db, test_user):
        """Test Legacy Divisions ReadList endpoint."""
        # First create a league and get divisions
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext

        RequestContext.set_datetime()
        try:
            league = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Test League",
                league_password="password",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[8, 10]
            )

            response = test_client.post(
                "/eff/eff_api/Divisions.php?f=ReadList",
                data={
                    "_format": "json",
                    "leagueID": str(league["leagueID"])
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "Divisions"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_divisions_readlist(self, test_client, test_db, test_user):
        """Test REST Divisions ReadList endpoint."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext

        RequestContext.set_datetime()
        try:
            league = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Test League",
                league_password="password",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[8, 10]
            )

            response = test_client.post(
                "/api/divisions/readlist",
                json={"leagueID": league["leagueID"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            RequestContext.reset()
