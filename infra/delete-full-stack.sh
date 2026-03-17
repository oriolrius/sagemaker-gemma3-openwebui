#!/bin/bash
# Delete full stack
#
# Usage:
#   ./delete-full-stack.sh [--stack-name name] [--region region] [--keep-s3]

set -e

STACK_NAME="openai-sagemaker-stack"
REGION="${AWS_REGION:-eu-west-1}"
KEEP_S3=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --keep-s3)
            KEEP_S3=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--stack-name name] [--region region] [--keep-s3]"
            echo ""
            echo "Options:"
            echo "  --stack-name    Stack name (default: openai-sagemaker-stack)"
            echo "  --region        AWS region (default: eu-west-1)"
            echo "  --keep-s3       Keep S3 bucket with Lambda artifacts"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get AWS account ID for S3 bucket name
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
LAMBDA_S3_BUCKET="${STACK_NAME}-lambda-${AWS_ACCOUNT_ID}-${REGION}"

echo "============================================"
echo "Deleting Full Stack"
echo "============================================"
echo "Stack Name: $STACK_NAME"
echo "Region:     $REGION"
echo "============================================"
echo ""
echo "This will delete:"
echo "  - SageMaker endpoint, config, and model"
echo "  - API Gateway and Lambda"
echo "  - EC2 instance and Elastic IP"
echo "  - IAM roles"
if [ "$KEEP_S3" = false ] && [ -n "$AWS_ACCOUNT_ID" ]; then
    echo "  - S3 bucket: $LAMBDA_S3_BUCKET"
fi
echo ""
read -p "Are you sure? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" &>/dev/null; then
    echo "Stack '$STACK_NAME' does not exist in $REGION"
    exit 0
fi

echo ""
echo "Deleting CloudFormation stack..."
echo "(This may take several minutes)"

aws cloudformation delete-stack \
    --region "$REGION" \
    --stack-name "$STACK_NAME"

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
    --region "$REGION" \
    --stack-name "$STACK_NAME"

echo "Stack deleted."

# Delete S3 bucket if requested
if [ "$KEEP_S3" = false ] && [ -n "$AWS_ACCOUNT_ID" ]; then
    if aws s3api head-bucket --bucket "$LAMBDA_S3_BUCKET" --region "$REGION" 2>/dev/null; then
        echo ""
        echo "Deleting S3 bucket: $LAMBDA_S3_BUCKET"
        aws s3 rb "s3://$LAMBDA_S3_BUCKET" --force --region "$REGION"
        echo "S3 bucket deleted."
    fi
fi

echo ""
echo "============================================"
echo "Cleanup complete!"
echo "============================================"
