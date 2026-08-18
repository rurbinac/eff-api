from datetime import datetime

from fastapi import APIRouter, Form, HTTPException

from app.actions.leagues import LeaguesBuildAction, LeaguesJoinAction
from app.actions.sign import (
    SignInfoAction,
    SignOutAction,
    SignUpAction,
    UpdateUserAction,
)
from app.actions.teams import (
    TeamsGetCurrentMembersAction,
    TeamsSetFranchiseWishListAction,
    TeamsSetRealMembersRankingAction,
    TeamsWaiverMembersDetailAction,
    TeamsWishListSetAction,
)
from app.context import RequestContext
from app.database import CurrentToken, CurrentUser, DbSession
from app.models import User

router = APIRouter()


@router.post("/gaming/api/SignInfo.php")
async def gaming_api_sign_info(db: DbSession, token: CurrentToken):
    """Gaming API SignInfo endpoint - token-based authentication."""
    RequestContext.set_datetime()
    try:
        if not token:
            return {"error": "Missing authentication token"}

        session_data = SignInfoAction.execute_with_token(db, token)

        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}
    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignOut.php")
async def gaming_api_sign_out(db: DbSession, current_user: CurrentUser):
    """Gaming API SignOut endpoint - token-based logout."""
    RequestContext.set_datetime()
    try:
        if current_user is None:
            return {"error": "Missing authentication token"}

        result = SignOutAction.execute(0)

        return {
            "table": "success",
            "values": result
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}
    finally:
        RequestContext.reset()


@router.post("/gaming/api/Users.php")
async def gaming_api_users(
    db: DbSession,
    current_user: CurrentUser,
    f: str | None = None,
    userID: int = Form(None),
    firstName: str = Form(None),
    lastName: str = Form(None),
    birthday: str = Form(default=None),
    country: str = Form(default=None),
    state: str = Form(default=None),
    city: str = Form(default=None),
    phoneNumber: str = Form(default=None),
    timeZone: str = Form(default=None),
    favoriteTeam: str = Form(default=None),
):
    """Gaming API Users endpoint - update user profile."""
    RequestContext.set_datetime()
    try:
        if f != "Update":
            return {"error": f"Unknown function: {f}"}

        if not userID:
            if current_user is None:
                return {"error": "Missing userID or authentication token"}
            userID = current_user

        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        session_data = UpdateUserAction.execute(
            db=db,
            user_id=userID,
            first_name=firstName,
            last_name=lastName,
            birthday=birthday_dt,
            country=country,
            state=state,
            city=city,
            phone_number=phoneNumber,
            time_zone=timeZone,
            favorite_team=favoriteTeam,
        )

        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignUp.php")
async def gaming_api_sign_up(
    db: DbSession,
    userEmail: str = Form(...),
    userPassword: str = Form(...),
    userName: str = Form(default=""),
    firstName: str = Form(...),
    lastName: str = Form(...),
    birthday: str = Form(default=None),
    country: str = Form(default=None),
    state: str = Form(default=None),
    city: str = Form(default=None),
    phoneNumber: str = Form(default=None),
    timeZone: str = Form(default=None),
    favoriteTeam: str = Form(default=None),
):
    """Gaming API SignUp endpoint - create new user account."""
    RequestContext.set_datetime()
    try:
        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        session_data = SignUpAction.execute(
            db=db,
            user_email=userEmail,
            user_password=userPassword,
            user_name=userName,
            first_name=firstName,
            last_name=lastName,
            birthday=birthday_dt,
            country=country if country else None,
            state=state if state else None,
            city=city if city else None,
            phone_number=phoneNumber if phoneNumber else None,
            time_zone=timeZone if timeZone else None,
            favorite_team=favoriteTeam if favoriteTeam else None,
        )

        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Leagues.php")
async def gaming_api_leagues(
    db: DbSession,
    current_user: CurrentUser,
    f: str | None = None,
    leagueName: str = Form(None),
    leaguePassword: str = Form(None),
    leagueType: int = Form(None),
    gameType: int = Form(None),
    scoringSystem: int = Form(None),
    tradeDeadline: str = Form(None),
    publishLeague: int = Form(None),
    seasonStatus: int = Form(None),
    teamsPerDivision: str = Form(None),
    leagueID: int = Form(None),
):
    """Gaming API Leagues endpoint - build or join league."""
    RequestContext.set_datetime()
    try:
        if f not in ("Build", "Join"):
            return {"error": f"Unknown function: {f}"}

        if current_user is None:
            return {"error": "Missing authentication token"}

        user = db.query(User).filter(User.userID == current_user).first()
        if not user:
            return {"error": "User not found"}

        if f == "Build":
            league_data = LeaguesBuildAction.execute(
                db=db,
                user_id=current_user,
                user_name=user.userName,
                league_name=leagueName,
                league_password=leaguePassword,
                league_type=leagueType,
                game_type=gameType,
                scoring_system=scoringSystem,
                trade_deadline=tradeDeadline,
                publish_league=publishLeague,
                season_status=seasonStatus,
                teams_per_division=teamsPerDivision,
            )
            return {
                "table": "Leagues",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": league_data
            }

        if f == "Join":
            team_data = LeaguesJoinAction.execute(
                db=db,
                user_id=current_user,
                league_id=leagueID,
                league_password=leaguePassword,
            )
            return {
                "table": "Teams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": team_data
            }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Teams.php")
async def gaming_api_teams(
    db: DbSession,
    current_user: CurrentUser,
    f: str | None = None,
    teamID: int = Form(None),
    memberKeys: str = Form(None),
    wishListKeys: str = Form(None),
    franchiseWishListKeys: str = Form(None),
):
    """Gaming API Teams endpoint - set/get member info."""
    RequestContext.set_datetime()
    try:
        if f == "GetCurrentMembers":
            if not teamID:
                return {"error": "teamID is required"}
            items = TeamsGetCurrentMembersAction.execute(db, teamID)
            return {
                "table": "RealTeamMembers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }

        elif f == "WaiverMembersDetail":
            if not teamID:
                return {"error": "teamID is required"}
            items = TeamsWaiverMembersDetailAction.execute(db, teamID)
            return {
                "table": "WaiverMembers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }

        elif f in ("SetRealMembersRanking", "WishListSet", "SetFranchiseWishList"):
            if current_user is None:
                return {"error": "Missing authentication token"}

            if f == "SetRealMembersRanking":
                if not teamID or not memberKeys:
                    return {"error": "teamID and memberKeys are required"}
                result = TeamsSetRealMembersRankingAction.execute(
                    db=db, team_id=teamID, user_id=current_user, member_keys_str=memberKeys,
                )
            elif f == "WishListSet":
                if not teamID or not wishListKeys:
                    return {"error": "teamID and wishListKeys are required"}
                result = TeamsWishListSetAction.execute(
                    db=db, team_id=teamID, user_id=current_user, wish_list_keys_str=wishListKeys,
                )
            else:  # SetFranchiseWishList
                if not teamID or not franchiseWishListKeys:
                    return {"error": "teamID and franchiseWishListKeys are required"}
                result = TeamsSetFranchiseWishListAction.execute(
                    db=db, team_id=teamID, user_id=current_user,
                    franchise_wish_list_keys_str=franchiseWishListKeys,
                )

            return {
                "table": "success",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": result
            }

        else:
            return {"error": f"Unknown function: {f}"}

    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()
