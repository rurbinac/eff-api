# EFF API - curl Test Suite

Comprehensive curl-based test suite for the EFF Fantasy Football API. These scripts are fully functional and reliable alternatives to the HTTP files in the `http/` folder.

## Why curl?

- ✅ Works reliably across all platforms (Windows, macOS, Linux)
- ✅ No VS Code REST Client issues
- ✅ Easy to automate and integrate into CI/CD
- ✅ Simple to debug and modify
- ✅ Tests both Legacy and REST API endpoints

## Quick Start

### Option 1: Run All Tests

```bash
# Make scripts executable
chmod +x *.sh

# Run all tests
bash run-all-tests.sh
```

### Option 2: Run Individual Tests

```bash
# Authentication tests
bash 01-legacy-auth.sh
bash 02-rest-auth.sh

# Data tests
bash 03-reference-data.sh
bash 04-league-data.sh
bash 05-match-data.sh
bash 06-standings.sh
```

## Configuration

Edit `variables.sh` to customize:

```bash
# Base URL
export BASE_URL="https://eff-api-150703383580.us-central1.run.app"

# Test credentials
export TEST_EMAIL="admin@effootball.com"
export TEST_PASSWORD="PASSWORD_1"

# Test data IDs
export TEST_LEAGUE_ID="63"
export TEST_DIVISION_ID="130"
export TEST_TEAM_ID="1187"
```

## Test Files

### 01-legacy-auth.sh
Tests legacy PHP-compatible authentication endpoints:
- `POST /eff/eff_api/Users.php?f=SignIn` - Sign in user
- `POST /eff/eff_api/Users.php?f=SignInfo` - Get user info
- `POST /eff/eff_api/Users.php?f=SignOut` - Sign out

### 02-rest-auth.sh
Tests REST API authentication endpoints:
- `POST /api/auth/signin` - Sign in user (REST)
- `POST /api/auth/signup` - Create new user
- `POST /api/auth/signout` - Sign out
- `PATCH /api/auth/users/{id}` - Update user profile

### 03-reference-data.sh
Tests reference/lookup data endpoints:
- `POST /eff/eff_api/Lookups.php?f=ReadList` - Legacy lookups
- `POST /api/lookups/readlist` - REST lookups (countries, states, etc.)

### 04-league-data.sh
Tests league, division, and team endpoints:
- `POST /eff/eff_api/Leagues.php?f=ReadList` - Legacy leagues
- `POST /api/leagues/readlist` - REST leagues
- `POST /eff/eff_api/Divisions.php?f=ReadList` - Legacy divisions
- `POST /api/divisions/readlist` - REST divisions
- `POST /api/teams/readlist` - REST teams
- `POST /api/divisionnotes/readlist` - Division notes

### 05-match-data.sh
Tests match-related endpoints:
- `POST /eff/eff_api/Matches.php?f=ReadList` - Legacy matches
- `POST /api/matches/readlist` - REST matches
- `POST /eff/eff_api/MatchTeams.php?f=ReadList` - Legacy match teams
- `POST /api/matchteams/readlist` - REST match teams
- `POST /eff/eff_api/RealMatches.php?f=ReadList` - Legacy real matches
- `POST /api/realmatches/readlist` - REST real matches

### 06-standings.sh
Tests standings endpoints:
- `POST /eff/eff_api/TeamStandings.php?f=ReadList` - Legacy team standings
- `POST /api/teamstandings/readlist` - REST team standings
- `POST /eff/eff_api/RealStandings.php?f=ReadList` - Legacy real standings
- `POST /api/realstandings/readlist` - REST real standings
- `POST /eff/eff_api/RealTeamStandings.php?f=ReadList` - Legacy real team standings
- `POST /api/realteamstandings/readlist` - REST real team standings

## Output Example

```
======================================
REST API - Authentication Tests
======================================

1. REST SignIn...
✓ REST SignIn (HTTP 200)
Response: {"userID":1,"userEmail":"admin@effootball.com",...}

Extracted token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

2. REST SignUp...
✓ REST SignUp (HTTP 200)
Response: {"userID":2,"userEmail":"curltest@test.com",...}
```

## Usage in CI/CD

```bash
#!/bin/bash
set -e  # Exit on error

cd curl/

# Run tests
bash run-all-tests.sh

echo "All API tests passed!"
```

## Troubleshooting

### Connection Refused
Check if the Cloud Run service is running:
```bash
gcloud run services list --region us-central1 --project eff-dev-497918
```

### Authentication Failed
Verify test credentials in `variables.sh`:
```bash
# Test the credentials directly
curl -X POST "https://eff-api-150703383580.us-central1.run.app/api/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{"userEmail":"admin@effootball.com","userPassword":"PASSWORD_1"}'
```

### JSON Parsing Issues
Install `jq` for better JSON parsing:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Windows (with chocolatey)
choco install jq
```

Then modify scripts to use `jq` for parsing:
```bash
AUTH_TOKEN=$(echo "$SIGNIN_RESPONSE" | jq -r '.token')
```

## Tips

1. **Extract tokens** from responses for authenticated requests:
   ```bash
   TOKEN=$(curl -s ... | grep -o '"token":"[^"]*' | cut -d'"' -f4)
   curl -H "Authorization: Bearer $TOKEN" ...
   ```

2. **Pretty print JSON** responses:
   ```bash
   curl -s ... | python -m json.tool
   ```

3. **Save responses** to file:
   ```bash
   curl -s ... > response.json
   ```

4. **Test with different parameters**:
   ```bash
   TEST_LEAGUE_ID=64 bash 04-league-data.sh
   ```

## API Response Format

### Legacy Endpoints (Form-based)
```json
{
  "table": "Session",
  "timestamp": "2026-06-17 02:35:51",
  "items": [
    {
      "values": {
        "userID": 1,
        "userEmail": "admin@effootball.com",
        ...
      }
    }
  ]
}
```

### REST Endpoints (JSON:API)
```json
{
  "data": [
    {
      "type": "lookups",
      "id": "3",
      "attributes": {
        "lookupID": 3,
        "lookupNum": 1,
        "position": 1,
        "lookupKey": "AF",
        "lookupCode": "AF",
        "lookupText": "Afghanistan"
      }
    }
  ],
  "meta": {
    "timestamp": "2026-06-17T03:17:25Z"
  }
}
```

## Support

For issues or questions:
1. Check that the Cloud Run service is active
2. Verify test credentials are correct
3. Ensure your firewall allows HTTPS (port 443)
4. Review curl output for specific error messages

## License

These test scripts are part of the EFF API project.
