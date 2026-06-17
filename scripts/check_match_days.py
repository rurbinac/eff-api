#!/usr/bin/env python3
"""Check MatchDaysStatus records in database."""
from google.cloud.sql.connector import Connector

connector = Connector()

try:
    with connector.connect("eff-dev-497918:us-central1:eff-dev-db", "pymysql") as conn:
        with conn.cursor() as cursor:
            # Check for MatchDaysStatus records for matchDayMapKey='21-35'
            query = """
            SELECT matchDayMapKey, matchDayID, scriptsStatus, startWaivers, finishWaivers,
                   startAuction, finishAuction, lockPlayerGames, startDayGamesForecast
            FROM MatchDaysStatus
            WHERE matchDayMapKey = '21-35'
            LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                print(f"Found {len(results)} MatchDaysStatus records for matchDayMapKey='21-35'")
                for row in results:
                    print(f"  matchDayID: {row[1]}")
                    print(f"  scriptsStatus: {row[2]}")
                    print(f"  startWaivers: {row[3]}")
                    print()
            else:
                print("No MatchDaysStatus records found for matchDayMapKey='21-35'")

                # Check what matchDayMapKeys exist
                query = """
                SELECT DISTINCT matchDayMapKey, COUNT(*) as count
                FROM MatchDaysStatus
                GROUP BY matchDayMapKey
                ORDER BY matchDayMapKey
                LIMIT 10
                """
                cursor.execute(query)
                results = cursor.fetchall()
                print(f"\nAvailable matchDayMapKeys:")
                for row in results:
                    print(f"  {row[0]}: {row[1]} records")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    connector.close()
