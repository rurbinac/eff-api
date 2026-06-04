import pytest


class TestTeamStandingsEndpoints:
    """Tests for team standings endpoints."""

    def test_legacy_team_standings_readlist(self, test_client, test_db, test_user):
        """Test Legacy TeamStandings ReadList endpoint."""
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
                    "/eff/eff_api/TeamStandings.php?f=ReadList",
                    data={
                        "_format": "json",
                        "teamID": str(team.teamID)
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["table"] == "TeamStandings"
                assert "timestamp" in data
                assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_team_standings_readlist(self, test_client, test_db, test_user):
        """Test REST TeamStandings ReadList endpoint."""
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
                    "/api/teamstandings/readlist",
                    json={"teamID": team.teamID}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            RequestContext.reset()


class TestRealStandingsEndpoints:
    """Tests for real standings endpoints."""

    def test_legacy_real_standings_readlist(self, test_client):
        """Test Legacy RealStandings ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/eff/eff_api/RealStandings.php?f=ReadList",
                data={
                    "_format": "json",
                    "realCompetitionID": "3",
                    "realCompetitionSeasonID": str(season_id)
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "RealStandings"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_real_standings_readlist(self, test_client):
        """Test REST RealStandings ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/api/realstandings/readlist",
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


class TestRealTeamStandingsEndpoints:
    """Tests for real team standings endpoints."""

    def test_legacy_real_team_standings_readlist(self, test_client):
        """Test Legacy RealTeamStandings ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/eff/eff_api/RealTeamStandings.php?f=ReadList",
                data={
                    "_format": "json",
                    "realCompetitionID": "3",
                    "realCompetitionSeasonID": str(season_id)
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["table"] == "RealTeamStandings"
            assert "timestamp" in data
            assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_real_team_standings_readlist(self, test_client):
        """Test REST RealTeamStandings ReadList endpoint."""
        from app.context import RequestContext
        from app.services import QueryService

        RequestContext.set_datetime()
        try:
            season_id = QueryService.get_season_id()

            response = test_client.post(
                "/api/realteamstandings/readlist",
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
