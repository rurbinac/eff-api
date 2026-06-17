#!/bin/bash

# League, Division, and Teams Tests

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "League, Division, and Teams Tests"
echo "======================================"
echo ""

# 1. Legacy Leagues ReadList
echo "1. Legacy Leagues ReadList..."
LEGACY_LEAGUES=$(curl -s -X POST "$LEGACY_API/Leagues.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byUserID&userID=$TEST_USER_ID")
LEGACY_LEAGUES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Leagues.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byUserID&userID=$TEST_USER_ID")

print_result "Legacy Leagues ReadList" "$LEGACY_LEAGUES_HTTP" "${LEGACY_LEAGUES:0:200}..."
echo ""

# 2. REST Leagues ReadList
echo "2. REST Leagues ReadList..."
REST_LEAGUES=$(curl -s -X POST "$REST_API/leagues/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"userID\":$TEST_USER_ID}")
REST_LEAGUES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/leagues/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"userID\":$TEST_USER_ID}")

print_result "REST Leagues ReadList" "$REST_LEAGUES_HTTP" "${REST_LEAGUES:0:200}..."
echo ""

# 3. Legacy Divisions ReadList
echo "3. Legacy Divisions ReadList..."
LEGACY_DIVISIONS=$(curl -s -X POST "$LEGACY_API/Divisions.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byLeagueID&leagueID=$TEST_LEAGUE_ID")
LEGACY_DIVISIONS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Divisions.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byLeagueID&leagueID=$TEST_LEAGUE_ID")

print_result "Legacy Divisions ReadList" "$LEGACY_DIVISIONS_HTTP" "${LEGACY_DIVISIONS:0:200}..."
echo ""

# 4. REST Divisions ReadList
echo "4. REST Divisions ReadList..."
REST_DIVISIONS=$(curl -s -X POST "$REST_API/divisions/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"leagueID\":$TEST_LEAGUE_ID}")
REST_DIVISIONS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/divisions/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"leagueID\":$TEST_LEAGUE_ID}")

print_result "REST Divisions ReadList" "$REST_DIVISIONS_HTTP" "${REST_DIVISIONS:0:200}..."
echo ""

# 5. Legacy Teams ReadList
echo "5. Legacy Teams ReadList (by Division)..."
LEGACY_TEAMS=$(curl -s -X POST "$LEGACY_API/Teams.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byDivisionID&divisionID=$TEST_DIVISION_ID")
LEGACY_TEAMS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Teams.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byDivisionID&divisionID=$TEST_DIVISION_ID")

print_result "Legacy Teams ReadList" "$LEGACY_TEAMS_HTTP" "${LEGACY_TEAMS:0:200}..."
echo ""

# 6. REST Teams ReadList
echo "6. REST Teams ReadList..."
REST_TEAMS=$(curl -s -X POST "$REST_API/teams/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")
REST_TEAMS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/teams/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")

print_result "REST Teams ReadList" "$REST_TEAMS_HTTP" "${REST_TEAMS:0:200}..."
echo ""

# 7. REST DivisionNotes ReadList
echo "7. REST DivisionNotes ReadList..."
REST_DIVISION_NOTES=$(curl -s -X POST "$REST_API/divisionnotes/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")
REST_DIVISION_NOTES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/divisionnotes/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")

print_result "REST DivisionNotes ReadList" "$REST_DIVISION_NOTES_HTTP" "${REST_DIVISION_NOTES:0:200}..."

echo "======================================"
echo "League Data Tests Complete"
echo "======================================"
