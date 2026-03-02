#!/bin/bash
# validate_appstore.sh - Validate all modules for Odoo Appstore compliance
# Usage: ./scripts/validate_appstore.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
TOTAL_MANIFESTS=0
VALID_MANIFESTS=0
TOTAL_HTML=0
VALID_HTML=0

echo "========================================="
echo "  Odoo Appstore Compliance Validator"
echo "========================================="
echo ""

# Check __manifest__.py files
echo "📋 Checking __manifest__.py files..."
echo ""

for manifest in $(find . -name "__manifest__.py" -type f | sort); do
    TOTAL_MANIFESTS=$((TOTAL_MANIFESTS + 1))
    ISSUES=()

    # Check for 'support' field
    if ! grep -q "'support'" "$manifest" && ! grep -q '"support"' "$manifest"; then
        ISSUES+=("Missing 'support' field")
    fi

    # Check for wrong support emails
    if grep -E "['\"]support['\"]:\s*['\"]support@brainstation-23\.com['\"]" "$manifest" > /dev/null 2>&1; then
        ISSUES+=("Wrong email: support@brainstation-23.com (use erp23@brainstation-23.com)")
    fi

    if grep -E "['\"]support['\"]:\s*['\"]odoo@brainstation-23\.com['\"]" "$manifest" > /dev/null 2>&1; then
        ISSUES+=("Wrong email: odoo@brainstation-23.com (use erp23@brainstation-23.com)")
    fi

    if grep -E "['\"]support['\"]:\s*['\"]sales@" "$manifest" > /dev/null 2>&1; then
        ISSUES+=("Wrong email: sales@ (use erp23@brainstation-23.com)")
    fi

    # Check for 'author' field
    if ! grep -q "'author'" "$manifest" && ! grep -q '"author"' "$manifest"; then
        ISSUES+=("Missing 'author' field")
    fi

    # Check for correct author name (Brain Station 23)
    if ! grep -E "['\"]author['\"]:\s*['\"]Brain Station 23['\"]" "$manifest" > /dev/null 2>&1; then
        if grep "author" "$manifest" > /dev/null 2>&1; then
            ISSUES+=("Wrong author: must be exactly 'Brain Station 23'")
        fi
    fi

    if [ ${#ISSUES[@]} -eq 0 ]; then
        VALID_MANIFESTS=$((VALID_MANIFESTS + 1))
        echo -e "${GREEN}✓${NC} $manifest"
    else
        FAILED=1
        echo -e "${RED}✗${NC} $manifest"
        for issue in "${ISSUES[@]}"; do
            echo -e "  ${YELLOW}→${NC} $issue"
        done
    fi
done

echo ""
echo "📄 Checking index.html files..."
echo ""

# Check index.html files
for html in $(find . -path "*/static/description/index.html" -type f | sort); do
    TOTAL_HTML=$((TOTAL_HTML + 1))
    ISSUES=()

    # Check for old emails in mailto links
    if grep -E "mailto:[^\"']*sales@brainstation-23" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains sales@brainstation-23 email")
    fi

    if grep -E "mailto:[^\"']*sales@nop-station" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains sales@nop-station.com email")
    fi

    if grep -E "mailto:[^\"']*odoo@brainstation-23" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains odoo@brainstation-23 email")
    fi

    if grep -E "mailto:[^\"']*support@brainstation-23" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains support@brainstation-23 email")
    fi

    if grep -E "mailto:[^\"']*odoo@bs23" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains odoo@bs23.com email")
    fi

    if grep -E "mailto:[^\"']*sales@bs23" "$html" > /dev/null 2>&1; then
        ISSUES+=("Contains sales@bs23.com email")
    fi

    if [ ${#ISSUES[@]} -eq 0 ]; then
        VALID_HTML=$((VALID_HTML + 1))
        echo -e "${GREEN}✓${NC} $html"
    else
        FAILED=1
        echo -e "${RED}✗${NC} $html"
        for issue in "${ISSUES[@]}"; do
            echo -e "  ${YELLOW}→${NC} $issue"
        done
    fi
done

# Summary
echo ""
echo "========================================="
echo "  Summary"
echo "========================================="
echo -e "Manifests: ${GREEN}$VALID_MANIFESTS${NC} / $TOTAL_MANIFESTS valid"
echo -e "HTML files: ${GREEN}$VALID_HTML${NC} / $TOTAL_HTML valid"
echo ""

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}❌ Validation FAILED${NC}"
    echo "Please fix the issues above before publishing to Appstore."
    exit 1
else
    echo -e "${GREEN}✅ All checks PASSED${NC}"
    echo "Modules are ready for Odoo Appstore."
    exit 0
fi
