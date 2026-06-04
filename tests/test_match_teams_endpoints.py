import pytest


class TestMatchTeamsEndpoints:
    """Tests for match teams endpoints."""

    def test_legacy_match_teams_readlist(self, test_client, test_db, test_user):
        """Test Legacy MatchTeams ReadList endpoint."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Match

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

            # Get first match
            match = test_db.scalar(select(Match).filter(Match.leagueID == league["leagueID"]).limit(1))

            if match:
                response = test_client.post(
                    "/eff/eff_api/MatchTeams.php?f=ReadList",
                    data={
                        "_format": "json",
                        "matchID": str(match.matchID)
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["table"] == "MatchTeams"
                assert "timestamp" in data
                assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_match_teams_readlist(self, test_client, test_db, test_user):
        """Test REST MatchTeams ReadList endpoint."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Match

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

            # Get first match
            match = test_db.scalar(select(Match).filter(Match.leagueID == league["leagueID"]).limit(1))

            if match:
                response = test_client.post(
                    "/api/matchteams/readlist",
                    json={"matchID": match.matchID}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            RequestContext.reset()

    def test_match_teams_datetime_serialization(self, test_client, test_db, test_user):
        """Test that MatchTeams datetime fields are properly serialized."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Match

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

            match = test_db.scalar(select(Match).filter(Match.leagueID == league["leagueID"]).limit(1))

            if match:
                response = test_client.post(
                    "/api/matchteams/readlist",
                    json={"matchID": match.matchID}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)

                # Verify datetime fields are ISO formatted strings
                for item in data:
                    # DateTime fields should be strings if present
                    if "matchDayDate" in item and item["matchDayDate"]:
                        assert isinstance(item["matchDayDate"], str)
        finally:
            RequestContext.reset()
