#!/bin/bash
# Code Formatting Script
# Automatically format code with Black, isort, and check with flake8

set -e  # Exit on error

echo "================================"
echo "Code Formatting & Linting Script"
echo "================================"
echo ""

# Activate virtual environment if it exists
if [ -d "beatforge-audio-extraction-service-local/bin" ]; then
    source beatforge-audio-extraction-service-local/bin/activate
fi

# Check if tools are installed
if ! command -v black &> /dev/null; then
    echo "Error: black is not installed. Run: pip install black isort flake8"
    exit 1
fi

# Parse arguments
CHECK_ONLY=false
FIX=false
TARGET="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

echo "Target: $TARGET"
echo ""

if [ "$CHECK_ONLY" = true ]; then
    echo "📋 CHECK MODE (no changes will be made)"
    echo ""

    echo "1️⃣  Checking code formatting with Black..."
    black --check --diff "$TARGET"
    echo "✅ Black check complete"
    echo ""

    echo "2️⃣  Checking import sorting with isort..."
    isort --check-only --diff "$TARGET"
    echo "✅ isort check complete"
    echo ""

    echo "3️⃣  Linting with flake8..."
    # First pass: Critical errors only (matches CI)
    echo "   Pass 1: Critical errors (E9,F63,F7,F82)..."
    flake8 "$TARGET" --select=E9,F63,F7,F82 --show-source --statistics || true

    # Second pass: All errors with max-complexity
    echo "   Pass 2: All errors..."
    flake8 "$TARGET" --max-complexity=10 --max-line-length=127 --statistics || true
    echo "✅ flake8 check complete"

else
    echo "🔧 FORMAT MODE (will modify files)"
    echo ""

    echo "1️⃣  Sorting imports with isort..."
    isort "$TARGET"
    echo "✅ Imports sorted"
    echo ""

    echo "2️⃣  Formatting code with Black..."
    black "$TARGET"
    echo "✅ Code formatted"
    echo ""

    if [ "$FIX" = true ]; then
        echo "3️⃣  Attempting to auto-fix flake8 issues..."
        # Install autoflake if not present
        if ! command -v autoflake &> /dev/null; then
            echo "   Installing autoflake..."
            pip install autoflake
        fi
        autoflake --in-place --remove-unused-variables --remove-all-unused-imports "$TARGET"
        echo "✅ Auto-fixed imports"
        echo ""
    fi

    echo "4️⃣  Final check with flake8..."
    flake8 "$TARGET" --select=E9,F63,F7,F82 --show-source --statistics || echo "⚠️  Some errors remain (see above)"
fi

echo ""
echo "================================"
echo "Done!"
echo "================================"
