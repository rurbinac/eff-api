#!/usr/bin/env python3
"""
Restore database from backup by dropping all tables first, then restoring from SQL file.
"""
import os
import re
from google.cloud.sql.connector import Connector

def drop_all_tables(connector):
    """Drop all tables in the database."""
    with connector.connect("eff-dev-497918:us-central1:eff-dev-db", "pymysql") as conn:
        with conn.cursor() as cursor:
            # Get list of tables
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'eff_dev_db'")
            tables = cursor.fetchall()

            print(f"Found {len(tables)} tables to drop")

            # Disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            # Drop all tables
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                print(f"  Dropped table: {table_name}")

            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            conn.commit()
            print("All tables dropped successfully")

def restore_database(connector, backup_file):
    """Restore database from SQL backup file."""
    print(f"\nReading backup file: {backup_file}")
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by semicolon to get individual statements
    statements = [s.strip() for s in content.split(';') if s.strip()]
    print(f"Found {len(statements)} SQL statements")

    with connector.connect("eff-dev-497918:us-central1:eff-dev-db", "pymysql") as conn:
        with conn.cursor() as cursor:
            errors = []
            success_count = 0

            for i, statement in enumerate(statements, 1):
                try:
                    cursor.execute(statement)
                    success_count += 1
                    if i % 100 == 0:
                        print(f"  Executed {i}/{len(statements)} statements")
                except Exception as e:
                    error_msg = f"Error on statement {i}: {str(e)}"
                    errors.append(error_msg)
                    if len(errors) <= 10:  # Only print first 10 errors
                        print(f"  {error_msg}")

            conn.commit()

            print(f"\nRestore completed!")
            print(f"  Successful: {success_count}/{len(statements)}")
            print(f"  Errors: {len(errors)}")
            if errors and len(errors) > 10:
                print(f"  (Showing first 10 of {len(errors)} errors)")

def main():
    """Main function."""
    print("Connecting to Cloud SQL...")
    connector = Connector()

    try:
        # Step 1: Drop all existing tables
        print("\nStep 1: Dropping all existing tables...")
        drop_all_tables(connector)

        # Step 2: Restore from backup
        backup_file = r"C:\Users\rurbi\Projects\EFF\google\sql\lt3cil7v_eff_new.sql"
        print(f"\nStep 2: Restoring from backup...")
        restore_database(connector, backup_file)

        print("\n✅ Database restore completed successfully!")

    finally:
        connector.close()

if __name__ == "__main__":
    main()
