import pytest


class TestTeamsEndpoints:
    """Tests for teams endpoints."""

    def test_legacy_teams_readlist_by_league(self, test_client, test_db, test_user):
        """Test Legacy Teams ReadList endpoint by league."""
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
                "/eff/eff_api/Teams.php?f=ReadList",
                data={
                    "_format": "json",
                    "_type": "byLeagueID",
                    "leagueID": str(league["leagueID"])
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "Teams"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_legacy_teams_readlist_by_division(self, test_client, test_db, test_user):
        """Test Legacy Teams ReadList endpoint by division."""
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
                teams_per_division=[8]
            )

            # Get first division ID
            divisions_response = test_client.post(
                "/api/divisions/readlist",
                json={"leagueID": league["leagueID"]}
            )
            divisions = divisions_response.json()
            if divisions:
                division_id = divisions[0]["divisionID"]

                response = test_client.post(
                    "/eff/eff_api/Teams.php?f=ReadList",
                    data={
                        "_format": "json",
                        "_type": "byDivisionID",
                        "divisionID": str(division_id)
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["table"] == "Teams"
                assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_teams_readlist_by_league(self, test_client, test_db, test_user):
        """Test REST Teams ReadList endpoint by league."""
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
                "/api/teams/readlist",
                json={"leagueID": league["leagueID"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            RequestContext.reset()
