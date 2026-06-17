#!/bin/bash

# Reference Data Tests (Lookups)

source "$(dirname "$0")/variables.sh"

echo "======================================"
echo "Reference Data Tests - Lookups"
echo "======================================"
echo ""

# 1. Legacy Lookups ReadList
echo "1. Legacy Lookups ReadList (Countries)..."
LEGACY_LOOKUPS=$(curl -s -X POST "$LEGACY_API/Lookups.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byLookupNum&lookupNum=$TEST_LOOKUP_TYPE")
LEGACY_LOOKUPS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LEGACY_API/Lookups.php?f=ReadList" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_format=json&_type=byLookupNum&lookupNum=$TEST_LOOKUP_TYPE")

print_result "Legacy Lookups ReadList" "$LEGACY_LOOKUPS_HTTP" "${LEGACY_LOOKUPS:0:200}..."
echo ""

# 2. REST Lookups ReadList
echo "2. REST Lookups ReadList..."
REST_LOOKUPS=$(curl -s -X POST "$REST_API/lookups/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"lookupType\":$TEST_LOOKUP_TYPE}")
REST_LOOKUPS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/lookups/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"lookupType\":$TEST_LOOKUP_TYPE}")

print_result "REST Lookups ReadList" "$REST_LOOKUPS_HTTP" "${REST_LOOKUPS:0:200}..."
echo ""

# 3. States Lookup
echo "3. REST Lookups ReadList - States (lookupType=3)..."
STATES_LOOKUPS=$(curl -s -X POST "$REST_API/lookups/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"lookupType\":3}")
STATES_LOOKUPS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_API/lookups/readlist" \
  -H "Content-Type: application/json" \
  -d "{\"lookupType\":3}")

print_result "REST Lookups - States" "$STATES_LOOKUPS_HTTP" "${STATES_LOOKUPS:0:200}..."

echo "======================================"
echo "Reference Data Tests Complete"
echo "======================================"
