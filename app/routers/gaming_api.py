from fastapi import APIRouter, Form, Depends, Header, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.context import RequestContext
from app.actions.sign import SignInfoAction, SignOutAction, SignUpAction, UpdateUserAction
from app.actions.leagues import LeaguesBuildAction, LeaguesJoinAction
from app.actions.teams import TeamsSetRealMembersRankingAction, TeamsGetCurrentMembersAction, TeamsWishListSetAction
from app.security import decode_token

router = APIRouter()


@router.post("/gaming/api/SignInfo.php")
async def gaming_api_sign_info(
    format: str = Form("json", alias="_format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API SignInfo endpoint - token-based authentication."""
    RequestContext.set_datetime()
    try:
        # Extract token from Authorization header (Bearer token)
        token = None
        if authorization:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization

        if not token:
            return {"error": "Missing authentication token"}

        # Get data from action
        session_data = SignInfoAction.execute_with_token(db, token)

        # Format as legacy PHP response
        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignOut.php")
async def gaming_api_sign_out(
    format: str = Form("json", alias="_format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API SignOut endpoint - token-based logout."""
    RequestContext.set_datetime()
    try:
        # Extract token from Authorization header
        token = None
        if authorization:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization

        if not token:
            return {"error": "Missing authentication token"}

        # Verify token is valid (just to confirm user is authenticated)
        payload = decode_token(token)
        if not payload:
            return {"error": "Invalid or expired token"}

        # Get data from action
        result = SignOutAction.execute(0)

        # Format as legacy PHP response
        return {
            "table": "success",
            "values": result
        }

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Users.php")
async def gaming_api_users(
    f: str = None,
    format: str = Form("json", alias="_format"),
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
    authorization: str = Header(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Gaming API Users endpoint - update user profile."""
    RequestContext.set_datetime()
    try:
        if f != "Update":
            return {"error": f"Unknown function: {f}"}

        # If userID not provided, try to get from token
        if not userID:
            token = None
            if authorization:
                if authorization.startswith("Bearer "):
                    token = authorization[7:]
                else:
                    token = authorization

            if not token:
                return {"error": "Missing userID or authentication token"}

            payload = decode_token(token)
            if not payload:
                return {"error": "Invalid or expired token"}

            userID = int(payload.get("sub"))

        # Parse birthday if provided
        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        # Get data from action
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

        # Format as legacy PHP response
        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/SignUp.php")
async def gaming_api_sign_up(
    format: str = Form("json", alias="_format"),
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
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Gaming API SignUp endpoint - create new user account."""
    RequestContext.set_datetime()
    try:
        # Parse birthday if provided
        birthday_dt = None
        if birthday:
            try:
                birthday_dt = datetime.fromisoformat(birthday)
            except ValueError:
                return {"error": "Invalid birthday format, use YYYY-MM-DD"}

        # Get client IP
        client_ip = request.client.host if request.client else "0.0.0.0"

        # Get data from action
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

        # Format as legacy PHP response
        return {
            "table": "Session",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Leagues.php")
async def gaming_api_leagues(
    f: str = None,
    format: str = Form("json", alias="_format"),
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
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API Leagues endpoint - build or join league."""
    RequestContext.set_datetime()
    try:
        if f not in ("Build", "Join"):
            return {"error": f"Unknown function: {f}"}

        # Extract token from Authorization header
        token = None
        if authorization:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
            else:
                token = authorization

        if not token:
            return {"error": "Missing authentication token"}

        # Verify token and get user ID
        payload = decode_token(token)
        if not payload:
            return {"error": "Invalid or expired token"}

        user_id = int(payload.get("sub"))

        # Get user from database
        from app.models import User
        user = db.query(User).filter(User.userID == user_id).first()
        if not user:
            return {"error": "User not found"}

        # Handle Build function
        if f == "Build":
            # Get data from action
            league_data = LeaguesBuildAction.execute(
                db=db,
                user_id=user_id,
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
            # Format as legacy PHP response
            return {
                "table": "Leagues",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": league_data
            }

        # Handle Join function
        if f == "Join":
            # Get data from action
            team_data = LeaguesJoinAction.execute(
                db=db,
                user_id=user_id,
                league_id=leagueID,
                league_password=leaguePassword,
            )
            # Format as legacy PHP response
            return {
                "table": "Teams",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": team_data
            }

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()


@router.post("/gaming/api/Teams.php")
async def gaming_api_teams(
    f: str = None,
    format: str = Form("json", alias="_format"),
    teamID: int = Form(None),
    memberKeys: str = Form(None),
    wishListKeys: str = Form(None),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Gaming API Teams endpoint - set/get member info."""
    RequestContext.set_datetime()
    try:
        if f == "GetCurrentMembers":
            if not teamID:
                return {"error": "teamID is required"}

            # Get data from action
            items = TeamsGetCurrentMembersAction.execute(db, teamID)

            # Format as legacy PHP response
            return {
                "table": "RealTeamMembers",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "items": [{"values": item} for item in items]
            }

        elif f == "SetRealMembersRanking":
            if not teamID or not memberKeys:
                return {"error": "teamID and memberKeys are required"}

            # Extract token from Authorization header
            token = None
            if authorization:
                if authorization.startswith("Bearer "):
                    token = authorization[7:]
                else:
                    token = authorization

            if not token:
                return {"error": "Missing authentication token"}

            # Verify token and get user ID
            payload = decode_token(token)
            if not payload:
                return {"error": "Invalid or expired token"}

            user_id = int(payload.get("sub"))

            # Get data from action
            result = TeamsSetRealMembersRankingAction.execute(
                db=db,
                team_id=teamID,
                user_id=user_id,
                member_keys_str=memberKeys,
            )

            # Format as legacy PHP response
            return {
                "table": "success",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": result
            }

        elif f == "WishListSet":
            if not teamID or not wishListKeys:
                return {"error": "teamID and wishListKeys are required"}

            # Extract token from Authorization header
            token = None
            if authorization:
                if authorization.startswith("Bearer "):
                    token = authorization[7:]
                else:
                    token = authorization

            if not token:
                return {"error": "Missing authentication token"}

            # Verify token and get user ID
            payload = decode_token(token)
            if not payload:
                return {"error": "Invalid or expired token"}

            user_id = int(payload.get("sub"))

            # Get data from action
            result = TeamsWishListSetAction.execute(
                db=db,
                team_id=teamID,
                user_id=user_id,
                wish_list_keys_str=wishListKeys,
            )

            # Format as legacy PHP response
            return {
                "table": "success",
                "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
                "values": result
            }

        else:
            return {"error": f"Unknown function: {f}"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        RequestContext.reset()
