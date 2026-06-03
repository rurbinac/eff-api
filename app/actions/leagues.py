from sqlalchemy.orm import Session

from app.services import QueryService
from app.context import RequestContext, extract_match_day_status
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
