#!/usr/bin/env bash
# =============================================================================
# run_tests.sh — Elite Job Agent v2 Test Runner
# Branch: feature/email-client
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_ROOT/.venv"
REPORTS_DIR="$PROJECT_ROOT/test_reports"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p "$REPORTS_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         Elite Job Agent v2 — Security Test Suite         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "▶ Timestamp : $TIMESTAMP"
echo "▶ Branch    : $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo "▶ Commit    : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo ""

# ---------------------------------------------------------------------------
# 1. Activate virtual environment
# ---------------------------------------------------------------------------
if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️  .venv not found — using system Python"
fi

PYTHON=$(command -v python3 || command -v python)

# ---------------------------------------------------------------------------
# 2. Install test dependencies (non-destructive)
# ---------------------------------------------------------------------------
echo ""
echo "── Installing test dependencies ─────────────────────────────"
"$PYTHON" -m pip install --quiet pytest pytest-cov bandit 2>&1 | tail -3

# ---------------------------------------------------------------------------
# 3. Syntax check all source files
# ---------------------------------------------------------------------------
echo ""
echo "── Syntax Validation (py_compile) ──────────────────────────"
SYNTAX_PASS=true
for f in security_vault.py email_client.py agents.py gui.py main.py; do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        if "$PYTHON" -m py_compile "$PROJECT_ROOT/$f" 2>&1; then
            echo "  ✅ $f"
        else
            echo "  ❌ $f SYNTAX ERROR"
            SYNTAX_PASS=false
        fi
    fi
done

# ---------------------------------------------------------------------------
# 4. Run pytest suite
# ---------------------------------------------------------------------------
echo ""
echo "── Running Pytest Suite ─────────────────────────────────────"
PYTEST_REPORT="$REPORTS_DIR/pytest_${TIMESTAMP}.txt"

set +e
"$PYTHON" -m pytest \
    "$PROJECT_ROOT/tests" \
    -v \
    --tb=short \
    --cov="$PROJECT_ROOT" \
    --cov-config="$PROJECT_ROOT/pytest.ini" \
    --cov-report=term-missing \
    --cov-report="html:$REPORTS_DIR/coverage_html_${TIMESTAMP}" \
    2>&1 | tee "$PYTEST_REPORT"
PYTEST_EXIT=$?
set -e

if [ $PYTEST_EXIT -eq 0 ]; then
    echo ""
    echo "  ✅ All tests passed"
else
    echo ""
    echo "  ⚠️  Some tests failed or had expected failures (xfail) — see report"
fi

# ---------------------------------------------------------------------------
# 5. Bandit static security scan
# ---------------------------------------------------------------------------
echo ""
echo "── Bandit Static Security Scan ──────────────────────────────"
BANDIT_REPORT="$REPORTS_DIR/bandit_${TIMESTAMP}.txt"

set +e
"$PYTHON" -m bandit \
    -r "$PROJECT_ROOT" \
    --exclude "$PROJECT_ROOT/tests,$PROJECT_ROOT/.venv,$PROJECT_ROOT/__pycache__" \
    -f txt \
    -o "$BANDIT_REPORT" \
    -ll 2>&1  # -ll = only medium and above
BANDIT_EXIT=$?
set -e

cat "$BANDIT_REPORT" 2>/dev/null || echo "(bandit report empty)"

if [ $BANDIT_EXIT -eq 0 ]; then
    echo "  ✅ Bandit: No medium/high severity issues"
else
    echo "  ⚠️  Bandit: Issues found (see $BANDIT_REPORT)"
fi

# ---------------------------------------------------------------------------
# 6. Hardcoded secrets grep
# ---------------------------------------------------------------------------
echo ""
echo "── Hardcoded Secrets Scan (grep) ────────────────────────────"
SECRETS_REPORT="$REPORTS_DIR/secrets_${TIMESTAMP}.txt"
SECRETS_FOUND=false

PATTERNS=(
    "sk-[A-Za-z0-9]{20,}"
    "gsk_[A-Za-z0-9]{20,}"
    "ghp_[A-Za-z0-9]{20,}"
    "AIza[A-Za-z0-9\-_]{35}"
)

for pat in "${PATTERNS[@]}"; do
    if grep -rE "$pat" \
        --include="*.py" \
        --exclude-dir=".venv" \
        --exclude-dir="__pycache__" \
        --exclude-dir="tests" \
        "$PROJECT_ROOT" 2>/dev/null >> "$SECRETS_REPORT"; then
        SECRETS_FOUND=true
    fi
done

if [ "$SECRETS_FOUND" = true ]; then
    echo "  ❌ Potential hardcoded secrets found:"
    cat "$SECRETS_REPORT"
else
    echo "  ✅ No hardcoded API keys or tokens detected in source"
fi

# ---------------------------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                     TEST SUMMARY                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Syntax Check  : $([ "$SYNTAX_PASS" = true ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "  Pytest        : $([ $PYTEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "⚠️  CHECK REPORT")"
echo "  Bandit        : $([ $BANDIT_EXIT -eq 0 ] && echo "✅ PASS" || echo "⚠️  ISSUES FOUND")"
echo "  Secrets Scan  : $([ "$SECRETS_FOUND" = false ] && echo "✅ CLEAN" || echo "❌ SECRETS FOUND")"
echo ""
echo "  Reports saved to: $REPORTS_DIR/"
echo "  • Pytest     : pytest_${TIMESTAMP}.txt"
echo "  • Bandit     : bandit_${TIMESTAMP}.txt"
echo "  • Coverage   : coverage_html_${TIMESTAMP}/"
echo "  • Secrets    : secrets_${TIMESTAMP}.txt"
echo ""
