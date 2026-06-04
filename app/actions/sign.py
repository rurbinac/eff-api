from datetime import datetime
from sqlalchemy.orm import Session

from app.models import User
from app.security import verify_password, create_access_token, hash_password, decode_token
from app.services import QueryService
from app.context import RequestContext
from app.constants import LookupNum
from fastapi import HTTPException, status


class SignInAction:
    """Sign in a user and return user data + context."""

    @staticmethod
    def _build_session_data(user: User, token: str | None = None) -> dict:
        """Build the session data for a user."""
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
        if token:
            session_data["token"] = token
        return session_data

    @staticmethod
    def _add_context_data(db: Session, session_data: dict) -> None:
        """Add RealCompetition, MatchDayStatus, and show data to session_data."""
        # Add RealCompetition context
        rc_data = QueryService.get_current_base_competition(db)
        if rc_data:
            session_data.update(rc_data)

        # Add MatchDayStatus context
        if "baseRealCompetitionID" in session_data:
            mds_data = QueryService.get_current_match_day_status(db, session_data["baseRealCompetitionID"])
            if mds_data:
                session_data.update(mds_data)

        # Add show data
        sd_data = QueryService.get_show_data(db)
        if sd_data:
            session_data.update(sd_data)

    @staticmethod
    def execute(db: Session, user_email: str, user_password: str, client_ip: str) -> dict:
        """Authenticate user and return signed-in data."""
        # Set request datetime in context
        request_datetime = RequestContext.get_datetime()

        user = db.query(User).filter(User.userEmail == user_email).first()

        if not user or not verify_password(user_password, user.userPassword):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update last sign in
        user.lastSignInDate = request_datetime
        user.lastSignInIP = client_ip
        db.commit()
        db.refresh(user)

        # Generate JWT token
        token = create_access_token({"sub": str(user.userID), "email": user.userEmail})

        # Build session data
        session_data = SignInAction._build_session_data(user, token)

        # Add context data
        SignInAction._add_context_data(db, session_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
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
        request_datetime = RequestContext.get_datetime()

        user = db.query(User).filter(User.userID == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build session data (no token for SignInfo)
        session_data = SignInAction._build_session_data(user)

        # Add context data
        SignInAction._add_context_data(db, session_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }

    @staticmethod
    def execute_with_token(db: Session, token: str) -> dict:
        """
        Verify token and return current user information with context.

        Used by /gaming/api/SignInfo.php endpoint.
        """
        request_datetime = RequestContext.get_datetime()

        # Decode and verify token
        payload = decode_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # Get user ID from token
        user_id = int(payload.get("sub"))

        user = db.query(User).filter(User.userID == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build session data (no token in response for token-based SignInfo)
        session_data = SignInAction._build_session_data(user)

        # Add context data
        SignInAction._add_context_data(db, session_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }


class UpdateUserAction:
    """Update user profile information."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        birthday: datetime | None = None,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
        phone_number: str | None = None,
        time_zone: str | None = None,
        favorite_team: str | None = None,
    ) -> dict:
        """Update user profile and return updated user info with context."""
        request_datetime = RequestContext.get_datetime()

        user = db.query(User).filter(User.userID == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Validate country and state if provided
        if country is not None and country:
            if not QueryService.validate_lookup(db, LookupNum.COUNTRY_CODE, country):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid country: {country}"
                )

        if state is not None and state:
            if not QueryService.validate_lookup(db, LookupNum.STATE_CODE, state):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state: {state}"
                )

        # Update only the provided fields
        if first_name is not None:
            user.firstName = first_name
        if last_name is not None:
            user.lastName = last_name
        if birthday is not None:
            user.birthday = birthday
        if country is not None:
            user.country = country if country else None
        if state is not None:
            user.state = state if state else None
        if city is not None:
            user.city = city if city else None
        if phone_number is not None:
            user.phoneNumber = phone_number if phone_number else None
        if time_zone is not None:
            user.timeZone = time_zone if time_zone else None
        if favorite_team is not None:
            user.favoriteTeam = favorite_team if favorite_team else None

        user.updatedIn = request_datetime
        db.commit()
        db.refresh(user)

        # Build session data (no token for update response)
        session_data = SignInAction._build_session_data(user)

        # Add context data
        SignInAction._add_context_data(db, session_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
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
        # Get request datetime from context
        request_datetime = RequestContext.get_datetime()

        # Check if user exists
        existing_user = db.query(User).filter(User.userEmail == user_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate country and state if provided
        if country and not QueryService.validate_lookup(db, LookupNum.COUNTRY_CODE, country):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid country: {country}"
            )

        if state and not QueryService.validate_lookup(db, LookupNum.STATE_CODE, state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state: {state}"
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
            createdIn=request_datetime,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate JWT token
        token = create_access_token({"sub": str(new_user.userID), "email": new_user.userEmail})

        # Build session data
        session_data = SignInAction._build_session_data(new_user, token)

        # Add context data
        SignInAction._add_context_data(db, session_data)

        # Return in PHP-compatible format
        return {
            "table": "Session",
            "timestamp": request_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "values": session_data
        }
