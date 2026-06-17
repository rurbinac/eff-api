#!/bin/bash

# EFF API Test Configuration

# Base URLs
export BASE_URL="https://eff-api-150703383580.us-central1.run.app"
export LEGACY_API="$BASE_URL/eff/eff_api"
export REST_API="$BASE_URL/api"

# Test Credentials
export TEST_EMAIL="nigel@bowmantx.com"
export TEST_PASSWORD="PASSWORD_9"
export TEST_USER_ID="1"

# New User for Testing
export NEW_USER_EMAIL="curltest@test.com"
export NEW_USER_PASSWORD="CurlPass123"

# League Test Data
export TEST_LEAGUE_ID="63"
export TEST_DIVISION_ID="130"
export TEST_TEAM_ID="1187"

# Real Data Test Parameters
export TEST_REAL_COMPETITION_ID="21"
export TEST_REAL_COMPETITION_SEASON_ID="38"
export TEST_LOOKUP_TYPE="2"
export TEST_MATCH_ID="1"

# Authentication tokens (set dynamically)
export AUTH_TOKEN=""
export NEW_USER_TOKEN=""
export NEW_USER_ID=""

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export NC='\033[0m' # No Color

# Helper function to print results
print_result() {
    local title=$1
    local http_code=$2
    local response=$3

    if [[ $http_code == 200 || $http_code == 201 ]]; then
        echo -e "${GREEN}✓ $title (HTTP $http_code)${NC}"
    else
        echo -e "${RED}✗ $title (HTTP $http_code)${NC}"
    fi
    echo "Response: $response"
    echo ""
}

# Helper function for API requests
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local content_type=${4:-"application/json"}
    local auth_header=$5

    local curl_cmd="curl -s -X $method '$endpoint' -H 'Content-Type: $content_type'"

    if [ -n "$auth_header" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $auth_header'"
    fi

    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi

    local response=$(eval "$curl_cmd")
    local http_code=$(eval "$curl_cmd -w '%{http_code}' -o /dev/null")

    echo "$response"
}
