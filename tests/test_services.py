import pytest
from datetime import datetime
from app.services import QueryService
from app.context import RequestContext
from app.constants import RealCompetitionConstants


class TestQueryService:
    """Tests for QueryService."""

    def test_get_season_id_current_month(self):
        """Test season ID calculation for current month."""
        # January (month 1) - should return previous year (season started in Aug of previous year)
        jan_date = datetime(2026, 1, 15)
        season = QueryService.get_season_id(jan_date)
        assert season == 2025

        # July (month 7) - should return previous year (season started in Aug of previous year)
        july_date = datetime(2026, 7, 15)
        season = QueryService.get_season_id(july_date)
        assert season == 2025

    def test_get_season_id_august_onward(self):
        """Test season ID calculation for August onwards."""
        # August (month 8) - should return current year (season starts in August)
        aug_date = datetime(2026, 8, 15)
        season = QueryService.get_season_id(aug_date)
        assert season == 2026

        # December (month 12) - should return current year (in same season that started in Aug)
        dec_date = datetime(2026, 12, 15)
        season = QueryService.get_season_id(dec_date)
        assert season == 2026

    def test_get_season_id_uses_context_datetime(self):
        """Test that get_season_id uses RequestContext datetime when not provided."""
        # Set context datetime to January (season started in previous August)
        RequestContext.set_datetime(datetime(2026, 1, 15))

        season = QueryService.get_season_id()
        assert season == 2025

        RequestContext.reset()

    def test_season_start_month_constant(self):
        """Test that SEASON_START_MONTH is set correctly."""
        assert RealCompetitionConstants.SEASON_START_MONTH == 8

    def test_base_and_extra_symid_constants(self):
        """Test that competition symbols are set correctly."""
        assert RealCompetitionConstants.BASE_SYMID == 'EN_PR'
        assert RealCompetitionConstants.EXTRA_SYMID == 'EN_FA'

    def test_get_season_id_edge_cases(self):
        """Test edge cases for season ID."""
        # Last day of July (still in season that started in Aug of previous year)
        july_31 = datetime(2026, 7, 31)
        assert QueryService.get_season_id(july_31) == 2025

        # First day of August (new season starts)
        aug_1 = datetime(2026, 8, 1)
        assert QueryService.get_season_id(aug_1) == 2026

    def test_get_season_id_different_years(self):
        """Test season ID across different years."""
        # 2025 January (season that started Aug 2024)
        assert QueryService.get_season_id(datetime(2025, 1, 1)) == 2024

        # 2025 August (season starts, returns 2025)
        assert QueryService.get_season_id(datetime(2025, 8, 1)) == 2025

        # 2027 May (season that started Aug 2026)
        assert QueryService.get_season_id(datetime(2027, 5, 15)) == 2026

        # 2027 October (season that started Aug 2027)
        assert QueryService.get_season_id(datetime(2027, 10, 15)) == 2027
