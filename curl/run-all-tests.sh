#!/bin/bash

# Master test runner - runs all curl test scripts

SCRIPT_DIR="$(dirname "$0")"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        EFF API - Complete Test Suite (curl)               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0

# Run each test script
run_test() {
    local script=$1
    echo ""
    echo "Running: $script..."
    echo "────────────────────────────────────────────────────────────"

    if bash "$SCRIPT_DIR/$script"; then
        ((PASSED_TESTS++))
    fi
    ((TOTAL_TESTS++))
}

# Run all tests
run_test "01-legacy-auth.sh"
run_test "02-rest-auth.sh"
run_test "03-reference-data.sh"
run_test "04-league-data.sh"
run_test "05-match-data.sh"
run_test "06-standings.sh"

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     Test Summary                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Total test scripts: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo ""
echo "✓ All tests completed!"
echo ""
