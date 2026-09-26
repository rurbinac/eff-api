from sqlalchemy.orm import Session

from app.exceptions import NotFoundException
from app.guards import require_league_member, require_team_owner
from app.models import DivisionNotes, Team, User
from app.services import QueryService
from app.utils.dt import utc_now


class DivisionNotesCreateAction:
    """Create a division note."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        team_id: int,
        title: str,
        division_note_type: str,
        notes: str | None = None,
        parent_division_note_id: int | None = None,
    ) -> dict:

        require_team_owner(db, user_id, team_id)
        team = db.get(Team, team_id)
        if not team:
            raise NotFoundException("Team", team_id)

        user = db.get(User, user_id)

        now = utc_now()
        note = DivisionNotes(
            leagueID=team.leagueID,
            divisionID=team.divisionID,
            teamID=team_id,
            userID=user_id,
            commissionerID=team.commissionerID,
            parentDivisionNoteID=parent_division_note_id,
            userName=user.userName if user else "",
            title=title,
            notes=notes,
            divisionNoteType=division_note_type,
            createdBy=user_id,
            createdIn=now,
            updatedBy=user_id,
            updatedIn=now,
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        return {
            "divisionNoteID": note.divisionNoteID,
            "leagueID": note.leagueID,
            "divisionID": note.divisionID,
            "teamID": note.teamID,
            "userID": note.userID,
            "commissionerID": note.commissionerID,
            "parentDivisionNoteID": note.parentDivisionNoteID,
            "userName": note.userName,
            "title": note.title,
            "notes": note.notes,
            "divisionNoteType": note.divisionNoteType,
            "createdBy": note.createdBy,
            "createdIn": note.createdIn.isoformat() if note.createdIn else None,
            "updatedBy": note.updatedBy,
            "updatedIn": note.updatedIn.isoformat() if note.updatedIn else None,
        }


class DivisionNotesUpdateAction:
    """Update a division note."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        division_note_id: int,
        title: str | None = None,
        notes: str | None = None,
    ) -> dict:
        note = db.get(DivisionNotes, division_note_id)
        if not note:
            raise NotFoundException("DivisionNotes", division_note_id)

        require_team_owner(db, user_id, note.teamID)

        if title is not None:
            note.title = title
        if notes is not None:
            note.notes = notes
        note.updatedBy = user_id
        note.updatedIn = utc_now()

        db.commit()
        db.refresh(note)

        return {
            "divisionNoteID": note.divisionNoteID,
            "leagueID": note.leagueID,
            "divisionID": note.divisionID,
            "teamID": note.teamID,
            "userID": note.userID,
            "commissionerID": note.commissionerID,
            "parentDivisionNoteID": note.parentDivisionNoteID,
            "userName": note.userName,
            "title": note.title,
            "notes": note.notes,
            "divisionNoteType": note.divisionNoteType,
            "createdBy": note.createdBy,
            "createdIn": note.createdIn.isoformat() if note.createdIn else None,
            "updatedBy": note.updatedBy,
            "updatedIn": note.updatedIn.isoformat() if note.updatedIn else None,
        }


class DivisionNotesDeleteAction:
    """Delete a division note."""

    @staticmethod
    def execute(db: Session, user_id: int, division_note_id: int) -> dict:
        note = db.get(DivisionNotes, division_note_id)
        if not note:
            raise NotFoundException("DivisionNotes", division_note_id)

        require_team_owner(db, user_id, note.teamID)

        db.delete(note)
        db.commit()

        return {"divisionNoteID": division_note_id}


class DivisionNotesReadListAction:
    """Get all notes for a division."""

    @staticmethod
    def execute(db: Session, division_id: int, user_id: int) -> list[dict]:
        """Get notes for a division."""
        require_league_member(db, user_id, division_id=division_id)
        # Query all notes for division
        return QueryService.get_division_notes(db, division_id)
