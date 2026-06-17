#!/bin/bash

# Match Data Tests

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "Match Data Tests"
echo "======================================"
echo ""

# 1. Legacy Matches ReadList
echo "1. Legacy Matches ReadList..."
LEGACY_MATCHES=$(curl -s -X POST "$LEGACY_API/Matches.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byDivisionID&divisionID=$TEST_DIVISION_ID")
LEGACY_MATCHES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Matches.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byDivisionID&divisionID=$TEST_DIVISION_ID")

print_result "Legacy Matches ReadList" "$LEGACY_MATCHES_HTTP" "${LEGACY_MATCHES:0:200}..."
echo ""

# 2. REST Matches ReadList
echo "2. REST Matches ReadList..."
REST_MATCHES=$(curl -s -X POST "$REST_API/matches/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")
REST_MATCHES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/matches/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"divisionID\":$TEST_DIVISION_ID}")

print_result "REST Matches ReadList" "$REST_MATCHES_HTTP" "${REST_MATCHES:0:200}..."
echo ""

# 3. Legacy MatchTeams ReadList
echo "3. Legacy MatchTeams ReadList..."
LEGACY_MATCH_TEAMS=$(curl -s -X POST "$LEGACY_API/MatchTeams.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byMatchID&matchID=$TEST_MATCH_ID")
LEGACY_MATCH_TEAMS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/MatchTeams.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byMatchID&matchID=$TEST_MATCH_ID")

print_result "Legacy MatchTeams ReadList" "$LEGACY_MATCH_TEAMS_HTTP" "${LEGACY_MATCH_TEAMS:0:200}..."
echo ""

# 4. REST MatchTeams ReadList
echo "4. REST MatchTeams ReadList..."
REST_MATCH_TEAMS=$(curl -s -X POST "$REST_API/matchteams/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"matchID\":$TEST_MATCH_ID}")
REST_MATCH_TEAMS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/matchteams/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"matchID\":$TEST_MATCH_ID}")

print_result "REST MatchTeams ReadList" "$REST_MATCH_TEAMS_HTTP" "${REST_MATCH_TEAMS:0:200}..."
echo ""

# 5. Legacy RealMatches ReadList
echo "5. Legacy RealMatches ReadList..."
LEGACY_REAL_MATCHES=$(curl -s -X POST "$LEGACY_API/RealMatches.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byCompetition&realCompetitionID=$TEST_REAL_COMPETITION_ID&realCompetitionMatchDay=$TEST_REAL_COMPETITION_SEASON_ID")
LEGACY_REAL_MATCHES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/RealMatches.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byCompetition&realCompetitionID=$TEST_REAL_COMPETITION_ID&realCompetitionMatchDay=$TEST_REAL_COMPETITION_SEASON_ID")

print_result "Legacy RealMatches ReadList" "$LEGACY_REAL_MATCHES_HTTP" "${LEGACY_REAL_MATCHES:0:200}..."
echo ""

# 6. REST RealMatches ReadList
echo "6. REST RealMatches ReadList..."
REST_REAL_MATCHES=$(curl -s -X POST "$REST_API/realmatches/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")
REST_REAL_MATCHES_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/realmatches/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")

print_result "REST RealMatches ReadList" "$REST_REAL_MATCHES_HTTP" "${REST_REAL_MATCHES:0:200}..."

echo "======================================"
echo "Match Data Tests Complete"
echo "======================================"
