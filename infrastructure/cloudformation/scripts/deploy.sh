#!/bin/bash
set -e

# MCP Infrastructure Deployment Script
# Deploys all CloudFormation stacks in the correct order

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="${SCRIPT_DIR}/../templates"
PARAMETERS_DIR="${SCRIPT_DIR}/../parameters"

# Default values (Ameritas environment codes: d=dev, t=test, m=model/staging, p=prod)
ENVIRONMENT="${ENVIRONMENT:-p}"
AWS_REGION="${AWS_REGION:-us-east-2}"
APP_NAME="${APP_NAME:-mcp}"
STACK_PREFIX="${APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment    Environment (prod, staging, dev). Default: prod"
    echo "  -r, --region         AWS Region. Default: us-east-2"
    echo "  -s, --stack          Deploy specific stack only"
    echo "  -v, --validate       Validate templates only, don't deploy"
    echo "  -d, --delete         Delete all stacks"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Available stacks (in deployment order):"
    echo "  1. iam              - IAM roles and policies"
    echo "  2. security-groups  - Security groups"
    echo "  3. cloud-map        - Service discovery namespace"
    echo "  4. ecs-cluster      - ECS cluster and log groups"
    echo "  5. nlb              - Network Load Balancer + PrivateLink"
    echo "  6. mcp-services     - All MCP ECS services"
    echo "  7. autoscaling      - Auto-scaling policies"
    echo ""
    echo "Examples:"
    echo "  $0 -e prod                    # Deploy all stacks to prod"
    echo "  $0 -e staging -s iam          # Deploy only IAM stack to staging"
    echo "  $0 -v                         # Validate all templates"
    echo "  $0 -d -e prod                 # Delete all prod stacks"
}

validate_templates() {
    log_info "Validating CloudFormation templates..."

    for template in "${TEMPLATES_DIR}"/*.yaml; do
        template_name=$(basename "$template")
        log_info "Validating ${template_name}..."
        aws cloudformation validate-template \
            --template-body "file://${template}" \
            --region "${AWS_REGION}" > /dev/null
        echo "  ✓ ${template_name} is valid"
    done

    log_info "All templates validated successfully!"
}

get_stack_status() {
    local stack_name=$1
    aws cloudformation describe-stacks \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "DOES_NOT_EXIST"
}

wait_for_stack() {
    local stack_name=$1
    local operation=$2  # create or update

    log_info "Waiting for stack ${stack_name} to complete ${operation}..."

    if [ "${operation}" == "create" ]; then
        aws cloudformation wait stack-create-complete \
            --stack-name "${stack_name}" \
            --region "${AWS_REGION}"
    else
        aws cloudformation wait stack-update-complete \
            --stack-name "${stack_name}" \
            --region "${AWS_REGION}"
    fi

    log_info "Stack ${stack_name} ${operation} completed!"
}

deploy_stack() {
    local stack_name=$1
    local template_file=$2
    local parameters=$3

    local full_stack_name="${STACK_PREFIX}-${stack_name}-${ENVIRONMENT}"
    local template_path="${TEMPLATES_DIR}/${template_file}"

    log_info "Deploying stack: ${full_stack_name}"

    local status=$(get_stack_status "${full_stack_name}")

    if [ "${status}" == "DOES_NOT_EXIST" ]; then
        log_info "Creating new stack..."
        aws cloudformation create-stack \
            --stack-name "${full_stack_name}" \
            --template-body "file://${template_path}" \
            --parameters ${parameters} \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "${AWS_REGION}" \
            --tags Key=Environment,Value="${ENVIRONMENT}" Key=Project,Value=mcp

        wait_for_stack "${full_stack_name}" "create"
    elif [[ "${status}" == *"COMPLETE"* ]] && [[ "${status}" != *"DELETE"* ]]; then
        log_info "Updating existing stack..."
        aws cloudformation update-stack \
            --stack-name "${full_stack_name}" \
            --template-body "file://${template_path}" \
            --parameters ${parameters} \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "${AWS_REGION}" 2>/dev/null || {
            if [ $? -eq 255 ]; then
                log_warn "No updates to be performed for ${full_stack_name}"
                return 0
            fi
        }

        wait_for_stack "${full_stack_name}" "update"
    else
        log_error "Stack ${full_stack_name} is in state ${status}, cannot deploy"
        return 1
    fi

    log_info "Stack ${full_stack_name} deployed successfully!"
}

get_stack_output() {
    local stack_name=$1
    local output_key=$2

    aws cloudformation describe-stacks \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}" \
        --query "Stacks[0].Outputs[?OutputKey=='${output_key}'].OutputValue" \
        --output text
}

load_parameters() {
    local param_file="${PARAMETERS_DIR}/${ENVIRONMENT}.json"

    if [ -f "${param_file}" ]; then
        log_info "Loading parameters from ${param_file}"
        cat "${param_file}"
    else
        log_warn "Parameter file ${param_file} not found, using defaults"
        echo "[]"
    fi
}

deploy_iam() {
    deploy_stack "iam" "iam-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT}"
}

deploy_security_groups() {
    local vpc_id="${VPC_ID:-$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION})}"
    local vpc_cidr="${VPC_CIDR:-10.0.0.0/16}"

    deploy_stack "security-groups" "security-groups-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=VpcId,ParameterValue=${vpc_id} ParameterKey=VpcCidr,ParameterValue=${vpc_cidr}"
}

deploy_cloud_map() {
    local vpc_id="${VPC_ID:-$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION})}"

    deploy_stack "cloud-map" "cloud-map-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=VpcId,ParameterValue=${vpc_id}"
}

deploy_ecs_cluster() {
    deploy_stack "ecs-cluster" "ecs-cluster-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT}"
}

deploy_nlb() {
    local vpc_id="${VPC_ID:-$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION})}"
    local private_subnets="${PRIVATE_SUBNET_IDS:-$(aws ec2 describe-subnets --filters Name=vpc-id,Values=${vpc_id} --query 'Subnets[?MapPublicIpOnLaunch==`false`].SubnetId' --output text --region ${AWS_REGION} | tr '\t' ',')}"
    local litellm_account="${LITELLM_ACCOUNT_ID:-}"

    deploy_stack "nlb" "nlb-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=VpcId,ParameterValue=${vpc_id} ParameterKey=PrivateSubnetIds,ParameterValue=\"${private_subnets}\" ParameterKey=LiteLLMAccountId,ParameterValue=${litellm_account}"
}

deploy_mcp_services() {
    # Get outputs from dependent stacks
    local iam_stack="${STACK_PREFIX}-iam-${ENVIRONMENT}"
    local sg_stack="${STACK_PREFIX}-security-groups-${ENVIRONMENT}"
    local cm_stack="${STACK_PREFIX}-cloud-map-${ENVIRONMENT}"
    local ecs_stack="${STACK_PREFIX}-ecs-cluster-${ENVIRONMENT}"
    local nlb_stack="${STACK_PREFIX}-nlb-${ENVIRONMENT}"

    local vpc_id="${VPC_ID:-$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION})}"
    local private_subnets="${PRIVATE_SUBNET_IDS:-$(aws ec2 describe-subnets --filters Name=vpc-id,Values=${vpc_id} --query 'Subnets[?MapPublicIpOnLaunch==`false`].SubnetId' --output text --region ${AWS_REGION} | tr '\t' ',')}"

    local ecr_uri="${ECR_REPOSITORY_URI:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com}"
    local image_tag="${IMAGE_TAG:-latest}"

    # This stack has many parameters - would typically be passed via parameter file
    log_info "Deploying MCP services stack..."
    log_warn "This stack requires many cross-stack references. Ensure dependent stacks are deployed."

    # For a full deployment, you would construct all parameters here
    # This is a simplified example
    deploy_stack "mcp-services" "mcp-services-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=VpcId,ParameterValue=${vpc_id} ParameterKey=PrivateSubnetIds,ParameterValue=\"${private_subnets}\" ParameterKey=ECRRepositoryUri,ParameterValue=${ecr_uri} ParameterKey=ImageTag,ParameterValue=${image_tag}"
}

deploy_autoscaling() {
    local ecs_stack="${STACK_PREFIX}-ecs-cluster-${ENVIRONMENT}"
    local iam_stack="${STACK_PREFIX}-iam-${ENVIRONMENT}"

    local cluster_name=$(get_stack_output "${ecs_stack}" "ClusterName")
    local autoscaling_role_arn=$(get_stack_output "${iam_stack}" "AutoScalingRoleArn")

    deploy_stack "autoscaling" "autoscaling-stack.yaml" \
        "ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=ECSClusterName,ParameterValue=${cluster_name} ParameterKey=AutoScalingRoleArn,ParameterValue=${autoscaling_role_arn}"
}

deploy_all() {
    log_info "Starting full deployment for environment: ${ENVIRONMENT}"

    deploy_iam
    deploy_security_groups
    deploy_cloud_map
    deploy_ecs_cluster
    deploy_nlb
    # deploy_mcp_services  # Uncomment when ready, requires all parameters
    # deploy_autoscaling   # Uncomment when services are deployed

    log_info "Deployment complete!"
    log_warn "Note: mcp-services and autoscaling stacks require additional configuration."
    log_warn "Please configure ECR_REPOSITORY_URI and other required parameters before deploying."
}

delete_stack() {
    local stack_name=$1
    local full_stack_name="${STACK_PREFIX}-${stack_name}-${ENVIRONMENT}"

    log_info "Deleting stack: ${full_stack_name}"

    aws cloudformation delete-stack \
        --stack-name "${full_stack_name}" \
        --region "${AWS_REGION}"

    log_info "Waiting for stack deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "${full_stack_name}" \
        --region "${AWS_REGION}"

    log_info "Stack ${full_stack_name} deleted!"
}

delete_all() {
    log_warn "Deleting all stacks for environment: ${ENVIRONMENT}"
    log_warn "This will delete resources in reverse order..."

    # Delete in reverse order
    delete_stack "autoscaling" 2>/dev/null || true
    delete_stack "mcp-services" 2>/dev/null || true
    delete_stack "nlb" 2>/dev/null || true
    delete_stack "ecs-cluster" 2>/dev/null || true
    delete_stack "cloud-map" 2>/dev/null || true
    delete_stack "security-groups" 2>/dev/null || true
    delete_stack "iam" 2>/dev/null || true

    log_info "All stacks deleted!"
}

# Parse arguments
VALIDATE_ONLY=false
DELETE_MODE=false
SPECIFIC_STACK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -s|--stack)
            SPECIFIC_STACK="$2"
            shift 2
            ;;
        -v|--validate)
            VALIDATE_ONLY=true
            shift
            ;;
        -d|--delete)
            DELETE_MODE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment (Ameritas codes: d=dev, t=test, m=model/staging, p=prod)
if [[ ! "${ENVIRONMENT}" =~ ^(d|t|m|p)$ ]]; then
    log_error "Invalid environment: ${ENVIRONMENT}"
    log_error "Valid values: d (dev), t (test), m (model/staging), p (prod)"
    exit 1
fi

log_info "Environment: ${ENVIRONMENT}"
log_info "Region: ${AWS_REGION}"

# Execute
if [ "${VALIDATE_ONLY}" == "true" ]; then
    validate_templates
elif [ "${DELETE_MODE}" == "true" ]; then
    delete_all
elif [ -n "${SPECIFIC_STACK}" ]; then
    case "${SPECIFIC_STACK}" in
        iam) deploy_iam ;;
        security-groups) deploy_security_groups ;;
        cloud-map) deploy_cloud_map ;;
        ecs-cluster) deploy_ecs_cluster ;;
        nlb) deploy_nlb ;;
        mcp-services) deploy_mcp_services ;;
        autoscaling) deploy_autoscaling ;;
        *)
            log_error "Unknown stack: ${SPECIFIC_STACK}"
            usage
            exit 1
            ;;
    esac
else
    deploy_all
fi
