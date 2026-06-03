import pytest
from datetime import datetime
from app.services import QueryService
from app.context import RequestContext


class TestQueryService:
    """Tests for QueryService."""

    def test_get_season_id_current_month(self):
        """Test season ID calculation for current month."""
        # January (month 1) - should return current year
        jan_date = datetime(2026, 1, 15)
        season = QueryService.get_season_id(jan_date)
        assert season == 2026

        # July (month 7) - should return current year
        july_date = datetime(2026, 7, 15)
        season = QueryService.get_season_id(july_date)
        assert season == 2026

    def test_get_season_id_august_onward(self):
        """Test season ID calculation for August onwards."""
        # August (month 8) - should return previous year
        aug_date = datetime(2026, 8, 15)
        season = QueryService.get_season_id(aug_date)
        assert season == 2025

        # December (month 12) - should return previous year
        dec_date = datetime(2026, 12, 15)
        season = QueryService.get_season_id(dec_date)
        assert season == 2025

    def test_get_season_id_uses_context_datetime(self):
        """Test that get_season_id uses RequestContext datetime when not provided."""
        # Set context datetime to January
        RequestContext.set_datetime(datetime(2026, 1, 15))

        season = QueryService.get_season_id()
        assert season == 2026

        RequestContext.reset()

    def test_season_start_month_constant(self):
        """Test that SEASON_START_MONTH is set correctly."""
        assert QueryService.SEASON_START_MONTH == 8

    def test_base_and_extra_symid_constants(self):
        """Test that competition symbols are set correctly."""
        assert QueryService.BASE_SYMID == 'EN_PR'
        assert QueryService.EXTRA_SYMID == 'EN_FA'

    def test_get_season_id_edge_cases(self):
        """Test edge cases for season ID."""
        # Last day of July
        july_31 = datetime(2026, 7, 31)
        assert QueryService.get_season_id(july_31) == 2026

        # First day of August
        aug_1 = datetime(2026, 8, 1)
        assert QueryService.get_season_id(aug_1) == 2025

    def test_get_season_id_different_years(self):
        """Test season ID across different years."""
        # 2025 January
        assert QueryService.get_season_id(datetime(2025, 1, 1)) == 2025

        # 2025 August
        assert QueryService.get_season_id(datetime(2025, 8, 1)) == 2024

        # 2027 May
        assert QueryService.get_season_id(datetime(2027, 5, 15)) == 2027

        # 2027 October
        assert QueryService.get_season_id(datetime(2027, 10, 15)) == 2026
