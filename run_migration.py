#!/usr/bin/env python3
"""Run the fix_matches.sql migration script."""

import sys
from sqlalchemy import text
from app.database import engine


def parse_sql_statements(sql_content):
    """Parse SQL file into individual statements, filtering comments."""
    statements = []
    current = []

    for line in sql_content.split('\n'):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('--'):
            continue

        current.append(line)

        # Check if line ends with semicolon
        if stripped.endswith(';'):
            stmt = '\n'.join(current).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current = []

    return statements


def run_migration():
    """Execute the migration script."""
    try:
        with open("fix_matches.sql", "r", encoding="utf-8") as f:
            sql_content = f.read()

        statements = parse_sql_statements(sql_content)
        print(f"Found {len(statements)} SQL statements\n")

        with engine.connect() as connection:
            # Clean up any leftover old tables from previous failed attempts
            cleanup_tables = [
                "DROP TABLE IF EXISTS `MatchTeams_old`",
                "DROP TABLE IF EXISTS `Matches_old`",
                "DROP TABLE IF EXISTS `RealMatchTeams_old`",
                "DROP TABLE IF EXISTS `RealMatches_old`"
            ]
            print("[0/36] Cleaning up leftover old tables...")
            for cleanup_stmt in cleanup_tables:
                try:
                    connection.execute(text(cleanup_stmt))
                    connection.commit()
                except Exception:
                    pass
            print("       [OK]\n")
            for i, statement in enumerate(statements, 1):
                try:
                    print(f"[{i}/{len(statements)}] Executing statement...")
                    connection.execute(text(statement))
                    connection.commit()
                    print(f"         [OK]")
                except Exception as e:
                    print(f"         [ERROR] {e}")
                    raise

        print(f"\n[SUCCESS] Migration completed successfully!")
        return 0

    except Exception as e:
        print(f"\n[FAILED] Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_migration())
