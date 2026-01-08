#!/bin/bash
set -e

# CloudFormation Template Validation Script
# Validates all templates and optionally runs cfn-lint

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="${SCRIPT_DIR}/../templates"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

AWS_REGION="${AWS_REGION:-us-east-2}"
ERRORS=0

log_info "Validating CloudFormation templates in ${TEMPLATES_DIR}"
log_info "Using AWS Region: ${AWS_REGION}"
echo ""

# Check if cfn-lint is available
USE_CFN_LINT=false
if command -v cfn-lint &> /dev/null; then
    USE_CFN_LINT=true
    log_info "cfn-lint found, will perform additional linting"
else
    log_warn "cfn-lint not found. Install with: pip install cfn-lint"
    log_warn "Falling back to AWS CLI validation only"
fi

echo ""
echo "================================================"
echo "       AWS CloudFormation Validation"
echo "================================================"
echo ""

for template in "${TEMPLATES_DIR}"/*.yaml; do
    template_name=$(basename "$template")
    echo -n "Validating ${template_name}... "

    # AWS CLI validation
    if aws cloudformation validate-template \
        --template-body "file://${template}" \
        --region "${AWS_REGION}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Valid"
    else
        echo -e "${RED}✗${NC} Invalid"
        log_error "Template validation failed for ${template_name}"
        aws cloudformation validate-template \
            --template-body "file://${template}" \
            --region "${AWS_REGION}" 2>&1 || true
        ((ERRORS++))
    fi
done

# Run cfn-lint if available
if [ "${USE_CFN_LINT}" == "true" ]; then
    echo ""
    echo "================================================"
    echo "       cfn-lint Validation"
    echo "================================================"
    echo ""

    for template in "${TEMPLATES_DIR}"/*.yaml; do
        template_name=$(basename "$template")
        echo "Linting ${template_name}..."

        lint_output=$(cfn-lint "${template}" 2>&1) || true
        if [ -n "${lint_output}" ]; then
            echo "${lint_output}"
            # Count errors (lines starting with E)
            error_count=$(echo "${lint_output}" | grep -c "^E" || true)
            if [ "${error_count}" -gt 0 ]; then
                ((ERRORS+=${error_count}))
            fi
        else
            echo -e "  ${GREEN}✓${NC} No issues found"
        fi
        echo ""
    done
fi

echo "================================================"
echo ""

if [ ${ERRORS} -gt 0 ]; then
    log_error "Validation completed with ${ERRORS} error(s)"
    exit 1
else
    log_info "All templates validated successfully!"
    exit 0
fi
