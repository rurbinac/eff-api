from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SignInRequest, SignUpRequest, UpdateUserRequest
from app.actions.sign import SignInAction, SignOutAction, SignInfoAction, SignUpAction, UpdateUserAction
from app.context import RequestContext
from app.models import MatchDaysStatus

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/debug/matchdays/{real_competition_id}")
def debug_matchdays(real_competition_id: int, db: Session = Depends(get_db)) -> dict:
    """DEBUG: Check MatchDaysStatus records for a given competition."""
    RequestContext.set_datetime()
    try:
        current_datetime = RequestContext.get_datetime()

        # Get all records for this competition, ordered by match day
        all_records = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.matchDayMapKey == str(real_competition_id)
        ).order_by(MatchDaysStatus.realCompetitionMatchDay).all()

        # Get records matching our current query
        matching_records = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.matchDayMapKey == str(real_competition_id),
            MatchDaysStatus.startMatchDay <= current_datetime,
            MatchDaysStatus.finishMatchDay > current_datetime
        ).all()

        return {
            "current_datetime": current_datetime.isoformat(),
            "competition_id": real_competition_id,
            "matchDayMapKey_filter": str(real_competition_id),
            "total_records": len(all_records),
            "matching_records": len(matching_records),
            "match_day_range": f"Days {min([r.realCompetitionMatchDay for r in all_records]) if all_records else 'N/A'} - {max([r.realCompetitionMatchDay for r in all_records]) if all_records else 'N/A'}",
            "first_record": {
                "matchDay": all_records[0].realCompetitionMatchDay,
                "startMatchDay": all_records[0].startMatchDay.isoformat() if all_records and all_records[0].startMatchDay else None,
                "finishMatchDay": all_records[0].finishMatchDay.isoformat() if all_records and all_records[0].finishMatchDay else None,
            } if all_records else None,
            "last_record": {
                "matchDay": all_records[-1].realCompetitionMatchDay,
                "startMatchDay": all_records[-1].startMatchDay.isoformat() if all_records and all_records[-1].startMatchDay else None,
                "finishMatchDay": all_records[-1].finishMatchDay.isoformat() if all_records and all_records[-1].finishMatchDay else None,
            } if all_records else None,
            "matching_record": {
                "matchDay": matching_records[0].realCompetitionMatchDay,
                "startMatchDay": matching_records[0].startMatchDay.isoformat() if matching_records and matching_records[0].startMatchDay else None,
                "finishMatchDay": matching_records[0].finishMatchDay.isoformat() if matching_records and matching_records[0].finishMatchDay else None,
                "scriptsStatus": matching_records[0].scriptsStatus if matching_records else None,
            } if matching_records else None,
        }
    finally:
        RequestContext.reset()


@router.post("/signin")
def rest_signin(payload: SignInRequest, http_request: Request, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Sign in user."""
    RequestContext.set_datetime()
    try:
        # Get client IP
        client_ip = http_request.client.host if http_request.client else "0.0.0.0"
        # Get data from action
        session_data = SignInAction.execute(db, payload.userEmail, payload.userPassword, client_ip)
        # Return as REST array
        return session_data
    finally:
        RequestContext.reset()


@router.post("/signout")
def rest_signout() -> dict:
    """REST endpoint: Sign out user."""
    return SignOutAction.execute(0)


@router.post("/signup")
def rest_signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> dict:
    """REST endpoint: Create new user account."""
    RequestContext.set_datetime()
    try:
        # Get data from action
        session_data = SignUpAction.execute(
            db=db,
            user_email=payload.userEmail,
            user_password=payload.userPassword,
            user_name=payload.userName,
            first_name=payload.firstName,
            last_name=payload.lastName,
            birthday=payload.birthday,
            country=payload.country,
            state=payload.state,
            city=payload.city,
            phone_number=payload.phoneNumber,
            time_zone=payload.timeZone,
            favorite_team=payload.favoriteTeam,
        )
        # Return as REST object
        return session_data
    finally:
        RequestContext.reset()


@router.patch("/users/{user_id}")
def rest_update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
) -> dict:
    """REST endpoint: Update user profile."""
    RequestContext.set_datetime()
    try:
        # Get data from action
        session_data = UpdateUserAction.execute(
            db=db,
            user_id=user_id,
            first_name=payload.firstName,
            last_name=payload.lastName,
            birthday=payload.birthday,
            country=payload.country,
            state=payload.state,
            city=payload.city,
            phone_number=payload.phoneNumber,
            time_zone=payload.timeZone,
            favorite_team=payload.favoriteTeam,
        )
        # Return as REST object
        return session_data
    finally:
        RequestContext.reset()
