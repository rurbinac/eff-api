import pytest


class TestMatchesEndpoints:
    """Tests for matches endpoints."""

    def test_legacy_matches_readlist_by_league(self, test_client, test_db, test_user):
        """Test Legacy Matches ReadList endpoint by league."""
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

            response = test_client.post(
                "/eff/eff_api/Matches.php?f=ReadList",
                data={
                    "_format": "json",
                    "_type": "byLeagueID",
                    "leagueID": str(league["leagueID"])
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "Matches"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_matches_readlist_by_league(self, test_client, test_db, test_user):
        """Test REST Matches ReadList endpoint by league."""
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

            response = test_client.post(
                "/api/matches/readlist",
                json={"leagueID": league["leagueID"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            RequestContext.reset()

    def test_legacy_matches_readlist_by_team(self, test_client, test_db, test_user):
        """Test Legacy Matches ReadList endpoint by team."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Team

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

            # Get first team
            team = test_db.scalar(select(Team).filter(Team.leagueID == league["leagueID"]).limit(1))

            if team:
                response = test_client.post(
                    "/eff/eff_api/Matches.php?f=ReadList",
                    data={
                        "_format": "json",
                        "_type": "byTeamID",
                        "teamID": str(team.teamID)
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["table"] == "Matches"
                assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()
