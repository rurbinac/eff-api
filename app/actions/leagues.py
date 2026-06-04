from datetime import timedelta
from random import shuffle
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import League, Division, Team
from app.services import QueryService
from app.context import RequestContext, extract_match_day_status
from app.constants import LookupNum, DraftConstants
from app.security import verify_password
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
        db.flush()
        db.refresh(new_league)

        # Fetch division type and draft type lookups
        division_types = QueryService.get_lookups_by_num(db, LookupNum.DIVISION_TYPE)
        draft_types = QueryService.get_lookups_by_num(db, LookupNum.DRAFT_TYPE)

        if not division_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No division types found in lookups"
            )

        if not draft_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No draft types found in lookups"
            )

        # Get first draft type (same for all divisions)
        first_draft_type = draft_types[0]['lookupKey']

        # Calculate draftDate (current date + 1 week)
        draft_date = request_datetime + timedelta(days=7)

        # Create Divisions and Teams
        divisions_created = []
        for division_index, num_teams in enumerate(teams_list):
            # Get divisionType from ordered list
            if division_index >= len(division_types):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough division types for {len(teams_list)} divisions"
                )

            division_type = division_types[division_index]['lookupKey']

            # Calculate availableTeams (first division: numTeams - 1, others: numTeams)
            available_teams = num_teams - 1 if division_index == 0 else num_teams

            # Create Division
            new_division = Division(
                baseRealCompetitionID=new_league.baseRealCompetitionID,
                extraRealCompetitionID=new_league.extraRealCompetitionID,
                leagueID=new_league.leagueID,
                commissionerID=new_league.commissionerID,
                season=new_league.season,
                seasonNum=new_league.seasonNum,
                leagueMatches=DraftConstants.MATCHES_NONE,
                divisionMatches=DraftConstants.MATCHES_NONE,
                draftType=first_draft_type,
                draftDate=draft_date,
                draftStatus=DraftConstants.DRAFT_STATUS_NOT_DRAFTED,
                draftTime=DraftConstants.DRAFT_TIME,
                draftingUsers='{}',
                draftingHooks=0,
                franchiseMembers='',
                totalTeams=new_league.totalTeams,
                numTeams=num_teams,
                availableTeams=available_teams,
                divisionType=division_type,
                waiverStatus=DraftConstants.WAIVER_STATUS_NO_WAIVER,
                createdBy=new_league.commissionerID,
                createdIn=request_datetime,
            )

            db.add(new_division)
            db.flush()
            db.refresh(new_division)

            # Generate shuffled lists for randomOrder and seedingC3
            shuffle_list = list(range(1, num_teams + 1))
            shuffle(shuffle_list)
            seedingc3_shuffle = list(range(1, num_teams + 1))
            shuffle(seedingc3_shuffle)

            # Create Teams for this Division
            teams_created = []
            for team_index in range(num_teams):
                sequential = team_index + 1

                # First team in first division is commissioner's team
                if division_index == 0 and team_index == 0:
                    team_user_id = user_id
                    is_commissioner = 1
                    team_name = f"{user_name}'s team"
                else:
                    team_user_id = None
                    is_commissioner = 0
                    team_name = f"Team {division_type} - {sequential}"

                # Create Team
                new_team = Team(
                    baseRealCompetitionID=new_league.baseRealCompetitionID,
                    extraRealCompetitionID=new_league.extraRealCompetitionID,
                    leagueID=new_league.leagueID,
                    divisionID=new_division.divisionID,
                    commissionerID=new_league.commissionerID,
                    userID=team_user_id,
                    season=new_league.season,
                    seasonNum=new_league.seasonNum,
                    leagueMatches=new_division.leagueMatches,
                    divisionMatches=new_division.divisionMatches,
                    draftOrder=sequential,
                    randomOrder=shuffle_list[team_index],
                    waiversOrder=num_teams - sequential + 1,
                    teamName=team_name,
                    teamMembers='',
                    draftMembers='',
                    membersRanking='',
                    membersWaivers='',
                    membersWishList='',
                    franchiseWishList='',
                    fantasyPoints=0,
                    teamRanking=0,
                    locked=0,
                    isCommissioner=is_commissioner,
                    cntEPLTeam=0,
                    cntPlayer=0,
                    cntGoalkeeper=0,
                    cntDefender=0,
                    cntMidfielder=0,
                    cntStriker=0,
                    cntAdd=0,
                    cntDrop=0,
                    cntWaiver=0,
                    seedingC1=sequential,
                    seedingC2=0,
                    seedingC3=seedingc3_shuffle[team_index],
                    createdBy=new_league.commissionerID,
                    createdIn=request_datetime,
                )

                db.add(new_team)
                teams_created.append({
                    'sequential': sequential,
                    'teamName': team_name,
                    'userID': team_user_id,
                    'isCommissioner': is_commissioner,
                })

            divisions_created.append({
                'divisionIndex': division_index,
                'divisionType': division_type,
                'numTeams': num_teams,
                'teams': teams_created,
            })

        # Commit all changes in transaction
        db.commit()

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
            "divisionsCreated": len(divisions_created),
            "teamsCreated": sum(len(d['teams']) for d in divisions_created),
        }

        return {
            "table": "Leagues",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": league_data
        }


class LeaguesJoinAction:
    """Join an existing league."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        league_id: int,
        league_password: str,
    ) -> dict:
        """
        Join a league by assigning user to an available team.

        Args:
            db: Database session
            user_id: Current user ID
            league_id: League to join
            league_password: Password to verify league access

        Returns:
            Dict with team, division, and league info
        """
        request_datetime = RequestContext.get_datetime()

        # Get the league
        league = db.query(League).filter(League.leagueID == league_id).first()

        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found"
            )

        # Verify password
        if not verify_password(league_password, league.leaguePassword):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid league password"
            )

        # Check for available teams with draft not started
        available_team_result = db.execute(
            text("""
                SELECT t.teamID, t.leagueID, t.divisionID, d.draftStatus
                FROM Teams t
                INNER JOIN Divisions d ON t.divisionID = d.divisionID
                WHERE t.leagueID = :leagueID
                  AND t.userID IS NULL
                ORDER BY t.divisionID, t.teamID
                LIMIT 1
            """),
            {"leagueID": league_id}
        ).first()

        if not available_team_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available teams in this league"
            )

        # Verify draft has not started
        if available_team_result[3] != DraftConstants.DRAFT_STATUS_NOT_DRAFTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Draft has already started in this division"
            )

        # Get the actual team object
        team_id = available_team_result[0]
        available_team = db.query(Team).filter(Team.teamID == team_id).first()

        # Get the division
        division = db.query(Division).filter(
            Division.divisionID == available_team.divisionID
        ).first()

        if not division:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Division not found"
            )

        # Assign team to user
        available_team.userID = user_id
        available_team.updatedIn = request_datetime

        # Decrement availableTeams in division
        division.availableTeams -= 1
        division.updatedIn = request_datetime

        # Decrement availableTeams in league
        league.availableTeams -= 1
        league.updatedIn = request_datetime

        # Commit transaction
        db.commit()
        db.refresh(available_team)
        db.refresh(division)
        db.refresh(league)

        # Build response
        team_data = {
            "teamID": available_team.teamID,
            "teamName": available_team.teamName,
            "userID": available_team.userID,
            "isCommissioner": available_team.isCommissioner,
            "leagueID": league.leagueID,
            "leagueName": league.leagueName,
            "divisionID": division.divisionID,
            "divisionType": division.divisionType,
            "numTeams": division.numTeams,
            "availableTeamsDivision": division.availableTeams,
            "availableTeamsLeague": league.availableTeams,
            "season": league.season,
            "seasonNum": league.seasonNum,
        }

        return {
            "table": "Teams",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": team_data
        }
