from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, RealCompetition, MatchDaysStatus
from app.security import verify_password, create_access_token, hash_password
from fastapi import HTTPException, status


class SignInAction:
    """Sign in a user and return user data + context."""

    @staticmethod
    def _get_season_id() -> int:
        """Calculate current season ID based on month."""
        SEASON_START_MONTH = 8
        now = datetime.utcnow()
        if now.month < SEASON_START_MONTH:
            return now.year
        else:
            return now.year - 1

    @staticmethod
    def _get_current_base_real_competition(db: Session) -> dict | None:
        """Get the current base RealCompetition (EN_PR)."""
        season_id = SignInAction._get_season_id()
        rc = db.query(RealCompetition).filter(
            RealCompetition.realCompetitionSYMID == 'EN_PR',
            RealCompetition.realCompetitionSeasonId == str(season_id)
        ).first()
        return {
            "baseRealCompetitionID": rc.realCompetitionID,
            "realCompetitionLastMatchDay": rc.realCompetitionLastMatchDay,
            "extraRealCompetitionID": rc.extraRealCompetitionID,
            "baseRealCompetitionMatchDayBeforeExtra": rc.realCompetitionExtraMatchDay,
            "useExtraRealCompetition": rc.useExtraRealCompetition,
        } if rc else None

    @staticmethod
    def _get_current_match_day_status(db: Session, base_real_competition_id: int) -> dict | None:
        """Get current MatchDayStatus for the base competition."""
        mds = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.baseRealCompetitionID == base_real_competition_id,
            MatchDaysStatus.active == True
        ).first()

        if not mds:
            return None

        return {
            "realCompetitionID": mds.realCompetitionID,
            "realCompetitionMatchDay": mds.realCompetitionMatchDay,
            "baseRealCompetitionMatchDay": mds.realCompetitionMatchDay,
            "matchDayStatus": mds.scriptsStatus,
            "matchDayStatusStart": mds.startMatchDay.isoformat() if mds.startMatchDay else None,
            "matchDayStatusFinish": mds.finishMatchDay.isoformat() if mds.finishMatchDay else None,
            "realCompetitionMatchDaySort": mds.realCompetitionMatchDaySort,
            "prevActiveRealCompetitionID": mds.prevActiveRealCompetitionID,
            "prevActiveRealCompetitionMatchDay": mds.prevActiveRealCompetitionMatchDay,
            "nextActiveRealCompetitionID": mds.nextActiveRealCompetitionID,
            "nextActiveRealCompetitionMatchDay": mds.nextActiveRealCompetitionMatchDay,
        }

    @staticmethod
    def _get_show_data(db: Session) -> dict | None:
        """Get current show data (what to display)."""
        sd = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.active == True
        ).first()

        if not sd:
            return None

        return {
            "showRealCompetitionID": sd.realCompetitionID,
            "showRealCompetitionMatchDay": sd.realCompetitionMatchDay,
        }

    @staticmethod
    def execute(db: Session, user_email: str, user_password: str, client_ip: str) -> dict:
        """Authenticate user and return signed-in data."""
        user = db.query(User).filter(User.userEmail == user_email).first()

        if not user or not verify_password(user_password, user.userPassword):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update last sign in
        user.lastSignInDate = datetime.utcnow()
        user.lastSignInIP = client_ip
        db.commit()
        db.refresh(user)

        # Build session data
        session_data = {
            "userID": user.userID,
            "userEmail": user.userEmail,
            "userName": user.userName,
            "userLevel": user.userLevel,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "birthday": user.birthday.isoformat() if user.birthday else None,
            "country": user.country,
            "state": user.state,
            "city": user.city,
            "phoneNumber": user.phoneNumber,
            "timeZone": user.timeZone,
            "userAvatar": user.userAvatar,
            "favoriteTeam": user.favoriteTeam,
            "lastSignInDate": user.lastSignInDate.isoformat() if user.lastSignInDate else None,
            "lastSignInIP": user.lastSignInIP,
            "createdIn": user.createdIn.isoformat() if user.createdIn else None,
            "updatedIn": user.updatedIn.isoformat() if user.updatedIn else None,
            "feedsMode": 0,
            "token": create_access_token({"sub": str(user.userID), "email": user.userEmail}),
        }

        # Add RealCompetition context
        rc_data = SignInAction._get_current_base_real_competition(db)
        if rc_data:
            session_data.update(rc_data)

        # Add MatchDayStatus context
        if "baseRealCompetitionID" in session_data:
            mds_data = SignInAction._get_current_match_day_status(db, session_data["baseRealCompetitionID"])
            if mds_data:
                session_data.update(mds_data)

        # Add show data
        sd_data = SignInAction._get_show_data(db)
        if sd_data:
            session_data.update(sd_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }


class SignOutAction:
    """Sign out a user (token invalidation handled on client side)."""

    @staticmethod
    def execute(user_id: int) -> dict:
        """Sign out successful response."""
        return {"success": True}


class SignInfoAction:
    """Get current signed-in user info."""

    @staticmethod
    def execute(db: Session, user_id: int) -> dict:
        """Return current user information with context."""
        user = db.query(User).filter(User.userID == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build same session data as SignIn
        session_data = {
            "userID": user.userID,
            "userEmail": user.userEmail,
            "userName": user.userName,
            "userLevel": user.userLevel,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "birthday": user.birthday.isoformat() if user.birthday else None,
            "country": user.country,
            "state": user.state,
            "city": user.city,
            "phoneNumber": user.phoneNumber,
            "timeZone": user.timeZone,
            "userAvatar": user.userAvatar,
            "favoriteTeam": user.favoriteTeam,
            "lastSignInDate": user.lastSignInDate.isoformat() if user.lastSignInDate else None,
            "lastSignInIP": user.lastSignInIP,
            "createdIn": user.createdIn.isoformat() if user.createdIn else None,
            "updatedIn": user.updatedIn.isoformat() if user.updatedIn else None,
            "feedsMode": 0,
        }

        # Add RealCompetition context
        rc_data = SignInAction._get_current_base_real_competition(db)
        if rc_data:
            session_data.update(rc_data)

        # Add MatchDayStatus context
        if "baseRealCompetitionID" in session_data:
            mds_data = SignInAction._get_current_match_day_status(db, session_data["baseRealCompetitionID"])
            if mds_data:
                session_data.update(mds_data)

        # Add show data
        sd_data = SignInAction._get_show_data(db)
        if sd_data:
            session_data.update(sd_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }


class SignUpAction:
    """Create a new user account."""

    @staticmethod
    def execute(
        db: Session,
        user_email: str,
        user_password: str,
        user_name: str,
        first_name: str,
        last_name: str,
        birthday: datetime,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
        phone_number: str | None = None,
        time_zone: str | None = None,
        favorite_team: str | None = None,
    ) -> dict:
        """Create new user and return signed-in data."""
        # Check if user exists
        existing_user = db.query(User).filter(User.userEmail == user_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        new_user = User(
            userEmail=user_email,
            userPassword=hash_password(user_password),
            userName=user_name,
            userLevel=1,  # LEVEL_NORMAL
            firstName=first_name,
            lastName=last_name,
            birthday=birthday,
            country=country,
            state=state,
            city=city,
            phoneNumber=phone_number,
            timeZone=time_zone,
            userAvatar=None,
            favoriteTeam=favorite_team,
            createdIn=datetime.utcnow(),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate JWT token
        token = create_access_token({"sub": str(new_user.userID), "email": new_user.userEmail})

        # Build session data
        session_data = {
            "userID": new_user.userID,
            "userEmail": new_user.userEmail,
            "userName": new_user.userName,
            "userLevel": new_user.userLevel,
            "firstName": new_user.firstName,
            "lastName": new_user.lastName,
            "birthday": new_user.birthday.isoformat() if new_user.birthday else None,
            "country": new_user.country,
            "state": new_user.state,
            "city": new_user.city,
            "phoneNumber": new_user.phoneNumber,
            "timeZone": new_user.timeZone,
            "userAvatar": new_user.userAvatar,
            "favoriteTeam": new_user.favoriteTeam,
            "lastSignInDate": new_user.lastSignInDate.isoformat() if new_user.lastSignInDate else None,
            "lastSignInIP": new_user.lastSignInIP,
            "createdIn": new_user.createdIn.isoformat() if new_user.createdIn else None,
            "updatedIn": new_user.updatedIn.isoformat() if new_user.updatedIn else None,
            "feedsMode": 0,
            "token": token,
        }

        # Add RealCompetition context
        rc_data = SignInAction._get_current_base_real_competition(db)
        if rc_data:
            session_data.update(rc_data)

        # Add MatchDayStatus context
        if "baseRealCompetitionID" in session_data:
            mds_data = SignInAction._get_current_match_day_status(db, session_data["baseRealCompetitionID"])
            if mds_data:
                session_data.update(mds_data)

        # Add show data
        sd_data = SignInAction._get_show_data(db)
        if sd_data:
            session_data.update(sd_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }
