from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User
from app.security import verify_password, create_access_token, hash_password
from fastapi import HTTPException, status


class SignInAction:
    """Sign in a user and return user data + JWT token."""

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

        # Generate JWT token
        token = create_access_token({"sub": str(user.userID), "email": user.userEmail})

        return {
            "userID": user.userID,
            "userEmail": user.userEmail,
            "userName": user.userName,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "userLevel": user.userLevel,
            "token": token,
            "feedsMode": 0
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
        """Return current user information."""
        user = db.query(User).filter(User.userID == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "userID": user.userID,
            "userEmail": user.userEmail,
            "userName": user.userName,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "userLevel": user.userLevel,
            "feedsMode": 0
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

        return {
            "userID": new_user.userID,
            "userEmail": new_user.userEmail,
            "userName": new_user.userName,
            "firstName": new_user.firstName,
            "lastName": new_user.lastName,
            "userLevel": new_user.userLevel,
            "token": token,
            "feedsMode": 0
        }
