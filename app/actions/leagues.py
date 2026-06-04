from sqlalchemy.orm import Session

from app.models import League
from app.services import QueryService
from app.context import RequestContext, extract_match_day_status
from app.constants import LookupNum
from fastapi import HTTPException, status


class LeaguesReadListAction:
    """Get all leagues where user has a team."""

    FIELDS_TO_REMOVE = {
        'startWaivers', 'finishWaivers', 'startWaiversSettle', 'finishWaiversSettle',
        'startOpenWaivers', 'finishOpenWaivers', 'startOpenWaiversSettle', 'finishOpenWaiversSettle',
        'startPreMatch', 'finishPreMatch', 'startMatch', 'finishMatch',
        'startPostMatch', 'finishPostMatch'
    }

    @staticmethod
    def execute(db: Session, user_id: int, season: int | None = None) -> dict:
        """Get leagues for user, with division and team info."""
        request_datetime = RequestContext.get_datetime()

        # Query all leagues with user's teams
        rows = QueryService.get_leagues_by_user(db, user_id)

        # Filter by season if provided, otherwise return all
        items = []
        for row in rows:
            if season is not None and row['season'] != season:
                continue

            # Extract and transform MatchDaysStatus fields
            match_day_data = {
                'scriptsStatus': row.get('scriptsStatus'),
                'startMatchDay': row.get('startMatchDay'),
                'finishMatchDay': row.get('finishMatchDay'),
            }
            match_day_transformed = extract_match_day_status(match_day_data)

            # Remove raw MatchDaysStatus fields
            cleaned_row = {k: v for k, v in row.items() if k not in LeaguesReadListAction.FIELDS_TO_REMOVE}

            # Add transformed match day fields
            cleaned_row.update(match_day_transformed)

            # Wrap in values dict
            items.append({"values": cleaned_row})

        return {
            "table": "Leagues",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items
        }


class LeaguesBuildAction:
    """Create a new league with divisions and teams."""

    # Constants for league creation
    MAX_DIVISIONS = 6

    MIN_EPL_TEAMS = 2
    MIN_PLAYERS = 14
    MIN_GOALKEEPER = 2
    MIN_DEFENDER = 5
    MIN_MIDFIELDER = 5
    MIN_STRIKER = 2

    MAX_EPL_TEAMS = 2
    MAX_PLAYERS = 17
    MAX_GOALKEEPER = 2
    MAX_DEFENDER = 7
    MAX_MIDFIELDER = 7
    MAX_STRIKER = 3

    AUTO_EPL_TEAMS = 1
    AUTO_GOALKEEPER = 1
    AUTO_DEFENDER = 4
    AUTO_MIDFIELDER = 4
    AUTO_STRIKER = 2

    MAX_WAIVERS = 3
    TOT_PROMOTED = 2
    MAX_FRANCHISE_MEMBERS = 2

    @staticmethod
    def _parse_teams_per_division(csv_str: str) -> list[int]:
        """Parse CSV string to list of ints and validate."""
        try:
            teams = [int(x.strip()) for x in csv_str.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="teamsPerDivision must be comma-separated integers"
            )

        # Validate each value is 8 or 10
        for t in teams:
            if t not in (8, 10):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each division must have 8 or 10 teams"
                )

        # Validate max 6 divisions
        if len(teams) > LeaguesBuildAction.MAX_DIVISIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {LeaguesBuildAction.MAX_DIVISIONS} divisions allowed"
            )

        return teams

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        user_name: str,
        league_name: str,
        league_password: str,
        league_type: int,
        game_type: int,
        scoring_system: int,
        trade_deadline: str,
        publish_league: int,
        season_status: int,
        teams_per_division: str,
    ) -> dict:
        """Create a new league with divisions and teams."""
        request_datetime = RequestContext.get_datetime()

        # Validate lookup fields against Lookups table
        if not QueryService.validate_lookup(db, LookupNum.LEAGUE_TYPE, league_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid leagueType: {league_type}"
            )

        if not QueryService.validate_lookup(db, LookupNum.GAME_TYPE, game_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid gameType: {game_type}"
            )

        if not QueryService.validate_lookup(db, LookupNum.LEAGUE_SCORING_SYSTEM, scoring_system):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scoringSystem: {scoring_system}"
            )

        if not QueryService.validate_lookup(db, LookupNum.SEASON_STATUS, season_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid seasonStatus: {season_status}"
            )

        # Parse and validate teamsPerDivision
        teams_list = LeaguesBuildAction._parse_teams_per_division(teams_per_division)

        # Calculate derived values
        total_teams = sum(teams_list)
        num_divisions = len(teams_list)
        available_teams = total_teams - 1

        # Get current season ID and baseRealCompetitionID
        season_id = QueryService.get_season_id()
        base_real_comp = QueryService.get_current_base_competition(db)

        if not base_real_comp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active competition found"
            )

        base_real_competition_id = base_real_comp.get('baseRealCompetitionID')

        # Parse trade deadline
        try:
            trade_deadline_dt = RequestContext.parse_datetime(trade_deadline)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid trade deadline format"
            )

        # Create League record
        new_league = League(
            baseRealCompetitionID=base_real_competition_id,
            leagueName=league_name,
            leaguePassword=league_password,
            commissionerID=user_id,
            season=season_id,
            seasonNum=1,
            numDivisions=num_divisions,
            leagueType=league_type,
            gameType=game_type,
            scoringSystem=scoring_system,
            tradeDeadline=trade_deadline_dt,
            publishLeague=publish_league,
            seasonStatus=season_status,
            totalTeams=total_teams,
            availableTeams=available_teams,
            totPromoted=LeaguesBuildAction.TOT_PROMOTED,
            maxFranchiseMembers=LeaguesBuildAction.MAX_FRANCHISE_MEMBERS,
            maxWaiver=LeaguesBuildAction.MAX_WAIVERS,
            minEPLTeam=LeaguesBuildAction.MIN_EPL_TEAMS,
            minPlayer=LeaguesBuildAction.MIN_PLAYERS,
            minGoalkeeper=LeaguesBuildAction.MIN_GOALKEEPER,
            minDefender=LeaguesBuildAction.MIN_DEFENDER,
            minMidfielder=LeaguesBuildAction.MIN_MIDFIELDER,
            minStriker=LeaguesBuildAction.MIN_STRIKER,
            maxEPLTeam=LeaguesBuildAction.MAX_EPL_TEAMS,
            maxPlayer=LeaguesBuildAction.MAX_PLAYERS,
            maxGoalkeeper=LeaguesBuildAction.MAX_GOALKEEPER,
            maxDefender=LeaguesBuildAction.MAX_DEFENDER,
            maxMidfielder=LeaguesBuildAction.MAX_MIDFIELDER,
            maxStriker=LeaguesBuildAction.MAX_STRIKER,
            autoEPLTeam=LeaguesBuildAction.AUTO_EPL_TEAMS,
            autoGoalkeeper=LeaguesBuildAction.AUTO_GOALKEEPER,
            autoDefender=LeaguesBuildAction.AUTO_DEFENDER,
            autoMidfielder=LeaguesBuildAction.AUTO_MIDFIELDER,
            autoStriker=LeaguesBuildAction.AUTO_STRIKER,
            createdBy=user_id,
            createdIn=request_datetime,
        )

        db.add(new_league)
        db.flush()  # Get the auto-generated leagueID without committing yet
        db.refresh(new_league)

        # Build response with league data
        league_data = {
            "leagueID": new_league.leagueID,
            "leagueName": new_league.leagueName,
            "leaguePassword": new_league.leaguePassword,
            "commissionerID": new_league.commissionerID,
            "commissionerName": user_name,
            "season": new_league.season,
            "seasonNum": new_league.seasonNum,
            "numDivisions": new_league.numDivisions,
            "totalTeams": new_league.totalTeams,
            "availableTeams": new_league.availableTeams,
            "leagueType": new_league.leagueType,
            "gameType": new_league.gameType,
            "scoringSystem": new_league.scoringSystem,
            "tradeDeadline": new_league.tradeDeadline.isoformat(),
            "publishLeague": new_league.publishLeague,
            "seasonStatus": new_league.seasonStatus,
            "baseRealCompetitionID": new_league.baseRealCompetitionID,
            "teamsPerDivision": teams_per_division,
        }

        return {
            "table": "Leagues",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": league_data
        }
