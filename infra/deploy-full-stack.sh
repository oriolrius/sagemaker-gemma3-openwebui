#!/bin/bash
# Deploy full stack: SageMaker TGI + API Gateway + Lambda + OpenWebUI on EC2
#
# Usage:
#   ./deploy-full-stack.sh --vpc-id vpc-xxx --subnet-id subnet-xxx [options]
#
# Required:
#   --vpc-id        VPC ID for EC2 instance
#   --subnet-id     Subnet ID for EC2 instance (must be public)
#
# Optional:
#   --stack-name    CloudFormation stack name (default: openai-sagemaker-stack)
#   --model-id      HuggingFace model ID (default: oriolrius/myemoji-gemma-3-270m-it)
#   --key-pair      EC2 Key Pair name for SSH access
#   --region        AWS region (default: eu-west-1)
#   --external-sagemaker-role-arn  Use existing SageMaker role (for Domain integration)
#
# Prerequisites:
#   - AWS CLI configured with credentials
#   - uv (Python package manager) installed

set -e

# Defaults
STACK_NAME="openai-sagemaker-stack"
MODEL_ID="oriolrius/myemoji-gemma-3-270m-it"
REGION="${AWS_REGION:-eu-west-1}"
SAGEMAKER_INSTANCE="ml.g5.xlarge"
EC2_INSTANCE="t3.small"
KEY_PAIR=""
VPC_ID=""
SUBNET_ID=""
LAMBDA_S3_BUCKET=""
EXTERNAL_SAGEMAKER_ROLE_ARN=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --model-id)
            MODEL_ID="$2"
            shift 2
            ;;
        --vpc-id)
            VPC_ID="$2"
            shift 2
            ;;
        --subnet-id)
            SUBNET_ID="$2"
            shift 2
            ;;
        --key-pair)
            KEY_PAIR="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --sagemaker-instance)
            SAGEMAKER_INSTANCE="$2"
            shift 2
            ;;
        --ec2-instance)
            EC2_INSTANCE="$2"
            shift 2
            ;;
        --lambda-s3-bucket)
            LAMBDA_S3_BUCKET="$2"
            shift 2
            ;;
        --external-sagemaker-role-arn)
            EXTERNAL_SAGEMAKER_ROLE_ARN="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --vpc-id vpc-xxx --subnet-id subnet-xxx [options]"
            echo ""
            echo "Required:"
            echo "  --vpc-id              VPC ID for EC2 instance"
            echo "  --subnet-id           Subnet ID (must be public subnet)"
            echo ""
            echo "Optional:"
            echo "  --stack-name          Stack name (default: openai-sagemaker-stack)"
            echo "  --model-id            HuggingFace model (default: oriolrius/myemoji-gemma-3-270m-it)"
            echo "  --key-pair            EC2 Key Pair for SSH"
            echo "  --region              AWS region (default: eu-west-1)"
            echo "  --sagemaker-instance  SageMaker instance (default: ml.g5.xlarge)"
            echo "  --ec2-instance        EC2 instance (default: t3.small)"
            echo "  --lambda-s3-bucket    S3 bucket for Lambda code (auto-created if not specified)"
            echo "  --external-sagemaker-role-arn  Use existing SageMaker role (for Domain integration)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$VPC_ID" ]; then
    echo "ERROR: --vpc-id is required"
    echo ""
    echo "Find your VPC ID with:"
    echo "  aws ec2 describe-vpcs --region $REGION --query 'Vpcs[*].[VpcId,Tags[?Key==\`Name\`].Value|[0]]' --output table"
    exit 1
fi

if [ -z "$SUBNET_ID" ]; then
    echo "ERROR: --subnet-id is required"
    echo ""
    echo "Find public subnets in your VPC with:"
    echo "  aws ec2 describe-subnets --region $REGION --filters Name=vpc-id,Values=$VPC_ID --query 'Subnets[?MapPublicIpOnLaunch==\`true\`].[SubnetId,AvailabilityZone]' --output table"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "Deploying Full Stack"
echo "============================================"
echo "Stack Name:         $STACK_NAME"
echo "Region:             $REGION"
echo "Model:              $MODEL_ID"
echo "SageMaker Instance: $SAGEMAKER_INSTANCE"
echo "EC2 Instance:       $EC2_INSTANCE"
echo "VPC ID:             $VPC_ID"
echo "Subnet ID:          $SUBNET_ID"
echo "Key Pair:           ${KEY_PAIR:-<none>}"
if [ -n "$EXTERNAL_SAGEMAKER_ROLE_ARN" ]; then
    echo "Integration Mode:   INTEGRATED (using external SageMaker role)"
    echo "External Role:      $EXTERNAL_SAGEMAKER_ROLE_ARN"
else
    echo "Integration Mode:   STANDALONE (creating own SageMaker role)"
fi
echo "============================================"
echo ""
echo "This will create:"
echo "  - SageMaker endpoint (~15-20 min to start)"
echo "  - API Gateway + Lambda"
echo "  - EC2 instance with OpenWebUI"
echo ""
echo "Estimated cost: ~\$0.80/hour (mostly SageMaker GPU)"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

#############################################
# Package Lambda Function
#############################################
echo ""
echo "Packaging Lambda function..."

LAMBDA_DIR="$SCRIPT_DIR/../lambda/openai-proxy"
BUILD_DIR="$SCRIPT_DIR/../.build"
LAMBDA_ZIP="lambda-openai-proxy.zip"
LAMBDA_S3_KEY="lambda/$STACK_NAME/$LAMBDA_ZIP"

# Clean and create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/package"

# Install dependencies using uv (boto3 is included in Lambda runtime, but install anyway for consistency)
echo "Installing Lambda dependencies..."
if command -v uv &> /dev/null; then
    uv pip install --target "$BUILD_DIR/package" boto3 --quiet
else
    pip install --target "$BUILD_DIR/package" boto3 --quiet
fi

# Copy source code
cp -r "$LAMBDA_DIR/src/"* "$BUILD_DIR/package/"

# Create zip file
echo "Creating Lambda deployment package..."
cd "$BUILD_DIR/package"
zip -r "../$LAMBDA_ZIP" . -q
cd "$SCRIPT_DIR"

echo "Lambda package created: $BUILD_DIR/$LAMBDA_ZIP"

#############################################
# Create/Verify S3 Bucket for Lambda
#############################################
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$LAMBDA_S3_BUCKET" ]; then
    LAMBDA_S3_BUCKET="${STACK_NAME}-lambda-${AWS_ACCOUNT_ID}-${REGION}"
fi

echo ""
echo "Using S3 bucket: $LAMBDA_S3_BUCKET"

# Create bucket if it doesn't exist
if ! aws s3api head-bucket --bucket "$LAMBDA_S3_BUCKET" --region "$REGION" 2>/dev/null; then
    echo "Creating S3 bucket for Lambda artifacts..."
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$LAMBDA_S3_BUCKET" \
            --region "$REGION"
    else
        aws s3api create-bucket \
            --bucket "$LAMBDA_S3_BUCKET" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
fi

# Upload Lambda package to S3
echo "Uploading Lambda package to S3..."
aws s3 cp "$BUILD_DIR/$LAMBDA_ZIP" "s3://$LAMBDA_S3_BUCKET/$LAMBDA_S3_KEY" --region "$REGION"

echo "Lambda uploaded to: s3://$LAMBDA_S3_BUCKET/$LAMBDA_S3_KEY"

#############################################
# Upload OpenWebUI Files to S3
#############################################
OPENWEBUI_DIR="$SCRIPT_DIR/../openwebui"

echo ""
echo "Uploading OpenWebUI files to S3..."
aws s3 cp "$OPENWEBUI_DIR/docker-compose.yml" "s3://$LAMBDA_S3_BUCKET/openwebui/docker-compose.yml" --region "$REGION"
aws s3 cp "$OPENWEBUI_DIR/setup.sh" "s3://$LAMBDA_S3_BUCKET/openwebui/setup.sh" --region "$REGION"

echo "OpenWebUI files uploaded to: s3://$LAMBDA_S3_BUCKET/openwebui/"

#############################################
# Build CloudFormation Parameters
#############################################
PARAMS="HuggingFaceModelId=$MODEL_ID"
PARAMS="$PARAMS SageMakerInstanceType=$SAGEMAKER_INSTANCE"
PARAMS="$PARAMS EC2InstanceType=$EC2_INSTANCE"
PARAMS="$PARAMS VpcId=$VPC_ID"
PARAMS="$PARAMS SubnetId=$SUBNET_ID"
PARAMS="$PARAMS LambdaS3Bucket=$LAMBDA_S3_BUCKET"
PARAMS="$PARAMS LambdaS3Key=$LAMBDA_S3_KEY"

if [ -n "$KEY_PAIR" ]; then
    PARAMS="$PARAMS EC2KeyPair=$KEY_PAIR"
fi

if [ -n "$EXTERNAL_SAGEMAKER_ROLE_ARN" ]; then
    PARAMS="$PARAMS ExternalSageMakerRoleArn=$EXTERNAL_SAGEMAKER_ROLE_ARN"
fi

# Deploy stack
echo ""
echo "Deploying CloudFormation stack..."
echo "(This will take 15-20 minutes for SageMaker endpoint)"
echo ""

aws cloudformation deploy \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --template-file "$SCRIPT_DIR/full-stack.yaml" \
    --parameter-overrides $PARAMS \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

# Get outputs
echo ""
echo "Getting stack outputs..."

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayEndpoint'].OutputValue" \
    --output text)

OPENWEBUI_URL=$(aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='OpenWebUIUrl'].OutputValue" \
    --output text)

EC2_IP=$(aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='EC2PublicIP'].OutputValue" \
    --output text)

ENDPOINT_NAME=$(aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='SageMakerEndpointName'].OutputValue" \
    --output text)

echo ""
echo "============================================"
echo "Deployment Complete!"
echo "============================================"
echo ""
echo "SageMaker Endpoint: $ENDPOINT_NAME"
echo "API Gateway:        $API_ENDPOINT"
echo "OpenWebUI:          $OPENWEBUI_URL"
echo "EC2 Public IP:      $EC2_IP"
echo ""
echo "============================================"
echo "Test Commands"
echo "============================================"
echo ""
echo "# Test API Gateway:"
echo "curl $API_ENDPOINT/v1/models"
echo ""
echo "# Chat completion:"
echo "curl -X POST $API_ENDPOINT/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"messages\": [{\"role\": \"user\", \"content\": \"The future of AI is\"}], \"max_tokens\": 50}'"
echo ""
echo "# Open WebUI in browser:"
echo "open $OPENWEBUI_URL"
echo ""
if [ -n "$KEY_PAIR" ]; then
    echo "# SSH to EC2:"
    echo "ssh -i ~/.ssh/$KEY_PAIR.pem ec2-user@$EC2_IP"
    echo ""
fi
echo "============================================"
echo "Cleanup"
echo "============================================"
echo ""
echo "To delete all resources:"
echo "  ./delete-full-stack.sh --stack-name $STACK_NAME --region $REGION"
echo ""
