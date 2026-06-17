#!/bin/bash

# Standings Tests

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "Standings Tests"
echo "======================================"
echo ""

# 1. Legacy TeamStandings ReadList
echo "1. Legacy TeamStandings ReadList..."
LEGACY_TEAM_STANDINGS=$(curl -s -X POST "$LEGACY_API/TeamStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json")
LEGACY_TEAM_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/TeamStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json")

print_result "Legacy TeamStandings ReadList" "$LEGACY_TEAM_STANDINGS_HTTP" "${LEGACY_TEAM_STANDINGS:0:200}..."
echo ""

# 2. REST TeamStandings ReadList
echo "2. REST TeamStandings ReadList..."
REST_TEAM_STANDINGS=$(curl -s -X POST "$REST_API/teamstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"teamID\":$TEST_TEAM_ID}")
REST_TEAM_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/teamstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"teamID\":$TEST_TEAM_ID}")

print_result "REST TeamStandings ReadList" "$REST_TEAM_STANDINGS_HTTP" "${REST_TEAM_STANDINGS:0:200}..."
echo ""

# 3. Legacy RealStandings ReadList
echo "3. Legacy RealStandings ReadList..."
LEGACY_REAL_STANDINGS=$(curl -s -X POST "$LEGACY_API/RealStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byCompetition&realCompetitionID=$TEST_REAL_COMPETITION_ID&realCompetitionMatchDay=$TEST_REAL_COMPETITION_SEASON_ID")
LEGACY_REAL_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/RealStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byCompetition&realCompetitionID=$TEST_REAL_COMPETITION_ID&realCompetitionMatchDay=$TEST_REAL_COMPETITION_SEASON_ID")

print_result "Legacy RealStandings ReadList" "$LEGACY_REAL_STANDINGS_HTTP" "${LEGACY_REAL_STANDINGS:0:200}..."
echo ""

# 4. REST RealStandings ReadList
echo "4. REST RealStandings ReadList..."
REST_REAL_STANDINGS=$(curl -s -X POST "$REST_API/realstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")
REST_REAL_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/realstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")

print_result "REST RealStandings ReadList" "$REST_REAL_STANDINGS_HTTP" "${REST_REAL_STANDINGS:0:200}..."
echo ""

# 5. Legacy RealTeamStandings ReadList
echo "5. Legacy RealTeamStandings ReadList..."
LEGACY_REAL_TEAM_STANDINGS=$(curl -s -X POST "$LEGACY_API/RealTeamStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byTeam&realCompetitionID=$TEST_REAL_COMPETITION_ID&realTeamID=1")
LEGACY_REAL_TEAM_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/RealTeamStandings.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byTeam&realCompetitionID=$TEST_REAL_COMPETITION_ID&realTeamID=1")

print_result "Legacy RealTeamStandings ReadList" "$LEGACY_REAL_TEAM_STANDINGS_HTTP" "${LEGACY_REAL_TEAM_STANDINGS:0:200}..."
echo ""

# 6. REST RealTeamStandings ReadList
echo "6. REST RealTeamStandings ReadList..."
REST_REAL_TEAM_STANDINGS=$(curl -s -X POST "$REST_API/realteamstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")
REST_REAL_TEAM_STANDINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/realteamstandings/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"realCompetitionID\":$TEST_REAL_COMPETITION_ID,\"realCompetitionSeasonID\":$TEST_REAL_COMPETITION_SEASON_ID}")

print_result "REST RealTeamStandings ReadList" "$REST_REAL_TEAM_STANDINGS_HTTP" "${REST_REAL_TEAM_STANDINGS:0:200}..."

echo "======================================"
echo "Standings Tests Complete"
echo "======================================"
