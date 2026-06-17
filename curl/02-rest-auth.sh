#!/bin/bash

# REST API - Authentication Tests

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "REST API - Authentication Tests"
echo "======================================"
echo ""

# 1. SignIn (REST)
echo "1. REST SignIn..."
SIGNIN_RESPONSE=$(curl -s -X POST "$REST_API/auth/signin" \
  -H "Content-Type: application/json" \
  -d "{\"userEmail\":\"$TEST_EMAIL\",\"userPassword\":\"$TEST_PASSWORD\"}")
SIGNIN_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/auth/signin" \
  -H "Content-Type: application/json" \
  -d "{\"userEmail\":\"$TEST_EMAIL\",\"userPassword\":\"$TEST_PASSWORD\"}")

print_result "REST SignIn" "$SIGNIN_HTTP" "$SIGNIN_RESPONSE"

# Extract token from response
AUTH_TOKEN=$(echo "$SIGNIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Extracted token: ${AUTH_TOKEN:0:50}..."
echo ""

# 2. SignUp (REST)
echo "2. REST SignUp..."
SIGNUP_RESPONSE=$(curl -s -X POST "$REST_API/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{
    \"userEmail\":\"$NEW_USER_EMAIL\",
    \"userPassword\":\"$NEW_USER_PASSWORD\",
    \"userName\":\"curluser1\",
    \"firstName\":\"Curl\",
    \"lastName\":\"Test\",
    \"birthday\":\"1990-01-15\",
    \"country\":\"US\",
    \"state\":\"CA\",
    \"city\":\"San Francisco\",
    \"phoneNumber\":\"555-0123\",
    \"timeZone\":\"America/Los_Angeles\",
    \"favoriteTeam\":\"Arsenal\"
  }")
SIGNUP_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{
    \"userEmail\":\"$NEW_USER_EMAIL\",
    \"userPassword\":\"$NEW_USER_PASSWORD\",
    \"userName\":\"curluser1\",
    \"firstName\":\"Curl\",
    \"lastName\":\"Test\"
  }")

print_result "REST SignUp" "$SIGNUP_HTTP" "$SIGNUP_RESPONSE"

# Extract new user token and ID
NEW_USER_TOKEN=$(echo "$SIGNUP_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
NEW_USER_ID=$(echo "$SIGNUP_RESPONSE" | grep -o '"userID":[0-9]*' | cut -d':' -f2)
echo "New user token: ${NEW_USER_TOKEN:0:50}..."
echo "New user ID: $NEW_USER_ID"
echo ""

# 3. SignOut (REST)
echo "3. REST SignOut..."
SIGNOUT_RESPONSE=$(curl -s -X POST "$REST_API/auth/signout" \
  -H "Content-Type: application/json" \
  -d '{}')
SIGNOUT_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/auth/signout" \
  -H "Content-Type: application/json" \
  -d '{}')

print_result "REST SignOut" "$SIGNOUT_HTTP" "$SIGNOUT_RESPONSE"

# 4. Update User (REST)
echo "4. REST Update User..."
UPDATE_RESPONSE=$(curl -s -X PATCH "$REST_API/auth/users/$NEW_USER_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"firstName\":\"CurlUpdated\",
    \"lastName\":\"TestUpdated\",
    \"country\":\"GB\",
    \"city\":\"London\",
    \"favoriteTeam\":\"Chelsea\",
    \"timeZone\":\"Europe/London\"
  }")
UPDATE_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$REST_API/auth/users/$NEW_USER_ID" \
  -H "Content-Type: application/json" \
  -d "{\"firstName\":\"CurlUpdated\"}")

print_result "REST Update User" "$UPDATE_HTTP" "$UPDATE_RESPONSE"

echo "======================================"
echo "REST Auth Tests Complete"
echo "======================================"
