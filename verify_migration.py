#!/usr/bin/env python3
"""Verify that the database migration was applied successfully."""

from sqlalchemy import text, inspect
from app.database import engine


def verify_migration():
    """Verify the migration was applied to Cloud SQL."""
    print("Verifying database migration...\n")

    with engine.connect() as connection:
        # Create inspector for table structure
        inspector = inspect(connection)

        # Check Matches table
        print("=" * 60)
        print("MATCHES TABLE")
        print("=" * 60)
        matches_columns = [col['name'] for col in inspector.get_columns('Matches')]
        print(f"Total columns: {len(matches_columns)}")
        print(f"\nColumns present: {', '.join(matches_columns[:10])}...")

        # Check for removed columns (should NOT exist)
        removed_columns = ['firstTeamID', 'firstTeamName', 'secondTeamID', 'secondTeamName']
        found_removed = [col for col in removed_columns if col in matches_columns]
        if found_removed:
            print(f"\n[ERROR] Found old columns that should be removed: {found_removed}")
        else:
            print(f"\n[OK] Old team columns successfully removed")

        # Check MatchTeams table
        print("\n" + "=" * 60)
        print("MATCHTEAMS TABLE")
        print("=" * 60)
        mt_columns = [col['name'] for col in inspector.get_columns('MatchTeams')]
        print(f"Total columns: {len(mt_columns)}")
        print(f"\nKey columns present: {', '.join([c for c in mt_columns if c in ['teamID', 'teamName', 'teamScore', 'lineup', 'place', 'won', 'lost']])}")

        # Check for standings columns (should exist)
        standings_columns = ['place', 'won', 'draw', 'lost', 'scoreFor', 'scoreAgainst', 'points']
        found_standings = [col for col in standings_columns if col in mt_columns]
        print(f"\nStandings fields found: {len(found_standings)}/{len(standings_columns)}")
        if len(found_standings) == len(standings_columns):
            print("[OK] All standings columns present in MatchTeams")
        else:
            print(f"[ERROR] Missing standings columns: {set(standings_columns) - set(found_standings)}")

        # Check RealMatches table
        print("\n" + "=" * 60)
        print("REALMATCHES TABLE")
        print("=" * 60)
        rm_columns = [col['name'] for col in inspector.get_columns('RealMatches')]
        print(f"Total columns: {len(rm_columns)}")

        # Check for removed columns
        removed_real = ['firstRealTeamID', 'firstRealTeamName', 'secondRealTeamID', 'secondRealTeamName']
        found_removed_real = [col for col in removed_real if col in rm_columns]
        if found_removed_real:
            print(f"\n[ERROR] Found old columns that should be removed: {found_removed_real}")
        else:
            print(f"\n[OK] Old real team columns successfully removed")

        # Check RealMatchTeams table
        print("\n" + "=" * 60)
        print("REALMATCHTEAMS TABLE")
        print("=" * 60)
        rmt_columns = [col['name'] for col in inspector.get_columns('RealMatchTeams')]
        print(f"Total columns: {len(rmt_columns)}")
        print(f"\nKey columns present: {', '.join([c for c in rmt_columns if c in ['realTeamID', 'realTeamName', 'realTeamScore', 'realTeamNumber']])}")

        # Check if table exists and has data
        result = connection.execute(text("SELECT COUNT(*) as cnt FROM RealMatchTeams"))
        count = result.scalar()
        print(f"Row count: {count}")
        if count > 0:
            print("[OK] RealMatchTeams table has data")
        else:
            print("[WARN] RealMatchTeams table is empty")

        # Check if old tables still exist (they shouldn't)
        print("\n" + "=" * 60)
        print("CLEANUP VERIFICATION")
        print("=" * 60)
        all_tables = inspector.get_table_names()
        old_tables = ['Matches_old', 'MatchTeams_old', 'RealMatches_old', 'RealMatchTeams_old']
        found_old = [t for t in old_tables if t in all_tables]

        if found_old:
            print(f"[ERROR] Old backup tables still exist: {found_old}")
        else:
            print("[OK] Old backup tables successfully removed")

        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)

        all_checks_passed = (
            len(found_removed) == 0 and
            len(found_removed_real) == 0 and
            len(found_old) == 0 and
            len(found_standings) == len(standings_columns)
        )

        if all_checks_passed:
            print("\n[SUCCESS] MIGRATION SUCCESSFULLY APPLIED!")
            print("\nDatabase schema has been normalized:")
            print("- Matches: metadata only (no team data)")
            print("- MatchTeams: team-specific data + standings")
            print("- RealMatches: metadata only (no team data)")
            print("- RealMatchTeams: per-team data")
            return True
        else:
            print("\n[FAILED] MIGRATION VERIFICATION FAILED!")
            print("Check the errors above")
            return False


if __name__ == "__main__":
    try:
        success = verify_migration()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Error connecting to database: {e}")
        exit(1)
