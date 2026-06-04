import pytest
from app.actions.leagues import LeaguesReadListAction, LeaguesBuildAction, LeaguesJoinAction
from app.context import RequestContext


class TestLeaguesReadListAction:
    """Tests for LeaguesReadListAction."""

    def test_read_list_by_user(self, test_db, test_user):
        """Test reading leagues for a user."""
        result = LeaguesReadListAction.execute(test_db, user_id=test_user.userID)

        assert isinstance(result, list)
        # Result should be pure data (no wrapper)

    def test_read_list_no_leagues(self, test_db, test_user):
        """Test reading leagues for user with no leagues."""
        result = LeaguesReadListAction.execute(test_db, user_id=99999)

        assert isinstance(result, list)
        assert len(result) == 0


class TestLeaguesBuildAction:
    """Tests for LeaguesBuildAction."""

    def test_build_league_success(self, test_db, test_user):
        """Test building a league."""
        RequestContext.set_datetime()
        try:
            result = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Test League",
                league_password="password123",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[8, 10]
            )

            assert isinstance(result, dict)
            assert "leagueID" in result
            assert result["leagueName"] == "Test League"
            assert result["numDivisions"] == 2
            assert result["totalTeams"] == 18
        finally:
            RequestContext.reset()

    def test_build_league_single_division(self, test_db, test_user):
        """Test building league with single division."""
        RequestContext.set_datetime()
        try:
            result = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Single Div League",
                league_password="password123",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[10]
            )

            assert isinstance(result, dict)
            assert result["numDivisions"] == 1
            assert result["totalTeams"] == 10
        finally:
            RequestContext.reset()


class TestLeaguesJoinAction:
    """Tests for LeaguesJoinAction."""

    def test_join_league_success(self, test_db, test_user):
        """Test joining a league."""
        RequestContext.set_datetime()
        try:
            # Create a league first
            league_result = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Join Test League",
                league_password="joinpass",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[8, 10]
            )
            league_id = league_result["leagueID"]

            # Join the league
            result = LeaguesJoinAction.execute(
                test_db,
                user_id=test_user.userID,
                league_id=league_id,
                league_password="joinpass"
            )

            assert isinstance(result, dict)
            assert result["leagueID"] == league_id
            assert result["userID"] == test_user.userID
        finally:
            RequestContext.reset()

    def test_join_league_wrong_password(self, test_db, test_user):
        """Test joining league with wrong password."""
        RequestContext.set_datetime()
        try:
            with pytest.raises(Exception):
                LeaguesJoinAction.execute(
                    test_db,
                    user_id=test_user.userID,
                    league_id=1,
                    league_password="wrongpass"
                )
        finally:
            RequestContext.reset()
