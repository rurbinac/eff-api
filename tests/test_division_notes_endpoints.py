import pytest


class TestDivisionNotesEndpoints:
    """Tests for division notes endpoints."""

    def test_legacy_division_notes_readlist(self, test_client, test_db, test_user):
        """Test Legacy DivisionNotes ReadList endpoint."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Division

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

            # Get first division
            division = test_db.scalar(select(Division).filter(Division.leagueID == league["leagueID"]).limit(1))

            if division:
                response = test_client.post(
                    "/eff/eff_api/DivisionNotes.php?f=ReadList",
                    data={
                        "_format": "json",
                        "divisionID": str(division.divisionID)
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["table"] == "DivisionNotes"
                assert "timestamp" in data
                assert isinstance(data["items"], list)
        finally:
            RequestContext.reset()

    def test_rest_division_notes_readlist(self, test_client, test_db, test_user):
        """Test REST DivisionNotes ReadList endpoint."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Division

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

            # Get first division
            division = test_db.scalar(select(Division).filter(Division.leagueID == league["leagueID"]).limit(1))

            if division:
                response = test_client.post(
                    "/api/divisionnotes/readlist",
                    json={"divisionID": division.divisionID}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            RequestContext.reset()

    def test_division_notes_empty(self, test_client, test_db, test_user):
        """Test reading division notes with no notes."""
        from app.actions.leagues import LeaguesBuildAction
        from app.context import RequestContext
        from sqlalchemy import select
        from app.models import Division

        RequestContext.set_datetime()
        try:
            league = LeaguesBuildAction.execute(
                test_db,
                user_id=test_user.userID,
                league_name="Empty Notes League",
                league_password="password",
                league_type=1,
                game_type=2,
                scoring_system=1,
                trade_deadline="2026-06-15 14:00:00",
                publish_league=1,
                season_status=1,
                teams_per_division=[8]
            )

            division = test_db.scalar(select(Division).filter(Division.leagueID == league["leagueID"]).limit(1))

            if division:
                response = test_client.post(
                    "/api/divisionnotes/readlist",
                    json={"divisionID": division.divisionID}
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                # Notes should be empty for new division
                assert len(data) == 0
        finally:
            RequestContext.reset()
