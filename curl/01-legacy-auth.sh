#!/bin/bash

# Legacy EFF API - Authentication Tests

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "Legacy EFF API - Authentication Tests"
echo "======================================"
echo ""

# 1. SignIn
echo "1. Legacy SignIn..."
SIGNIN_RESPONSE=$(curl -s -X POST "$LEGACY_API/Users.php?f=SignIn" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userEmail=$TEST_EMAIL&userPassword=$TEST_PASSWORD")
SIGNIN_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Users.php?f=SignIn" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userEmail=$TEST_EMAIL&userPassword=$TEST_PASSWORD")

print_result "Legacy SignIn" "$SIGNIN_HTTP" "$SIGNIN_RESPONSE"

# Extract token from response
AUTH_TOKEN=$(echo "$SIGNIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Extracted token: ${AUTH_TOKEN:0:50}..."
echo ""

# 2. SignInfo (with userID)
echo "2. Legacy SignInfo (with userID)..."
SIGNINFO_RESPONSE=$(curl -s -X POST "$LEGACY_API/Users.php?f=SignInfo" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userID=$TEST_USER_ID")
SIGNINFO_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Users.php?f=SignInfo" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userID=$TEST_USER_ID")

print_result "Legacy SignInfo" "$SIGNINFO_HTTP" "$SIGNINFO_RESPONSE"

# 3. SignInfo with Authorization header
echo "3. Legacy SignInfo (with Authorization header)..."
SIGNINFO_AUTH_RESPONSE=$(curl -s -X POST "$LEGACY_API/Users.php?f=SignInfo" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "_format=json")
SIGNINFO_AUTH_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Users.php?f=SignInfo" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "_format=json")

print_result "Legacy SignInfo (with token)" "$SIGNINFO_AUTH_HTTP" "$SIGNINFO_AUTH_RESPONSE"

# 4. SignOut
echo "4. Legacy SignOut..."
SIGNOUT_RESPONSE=$(curl -s -X POST "$LEGACY_API/Users.php?f=SignOut" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userID=$TEST_USER_ID")
SIGNOUT_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Users.php?f=SignOut" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&userID=$TEST_USER_ID")

print_result "Legacy SignOut" "$SIGNOUT_HTTP" "$SIGNOUT_RESPONSE"

echo "======================================"
echo "Legacy Auth Tests Complete"
echo "======================================"
