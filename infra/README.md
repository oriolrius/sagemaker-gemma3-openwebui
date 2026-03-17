# Infrastructure

CloudFormation templates for deploying a SageMaker TGI (HuggingFace Text Generation Inference) endpoint with OpenAI-compatible API.

## Deployment Modes

This stack supports two deployment modes:

| Mode | Use Case | SageMaker Role | Documentation |
|------|----------|----------------|---------------|
| **Standalone** | Independent deployment, no existing infrastructure | Created by stack | [STANDALONE.md](STANDALONE.md) |
| **Integrated** | Deploy within existing SageMaker Domain | Uses external role | [INTEGRATED.md](INTEGRATED.md) |

### Quick Comparison

| Aspect | Standalone | Integrated |
|--------|------------|------------|
| SageMaker Domain required | No | **Yes** (must exist) |
| SageMaker execution role | Created | Reused from Domain |
| Visible in SageMaker Studio | No | Yes |
| Shares resources with training | No | Yes |
| Cleanup | Deletes everything | Keeps Domain/role |

## Quick Start

### Standalone (Default)

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx
```

### Integrated (with existing SageMaker Domain)

```bash
# Get role ARN from existing Domain
ROLE_ARN=$(aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query 'DefaultUserSettings.ExecutionRole' \
  --output text)

# Deploy with external role
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx \
  --external-sagemaker-role-arn "$ROLE_ARN"
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌─────────────────┐
│  OpenWebUI  │────▶│ API Gateway  │────▶│   Lambda   │────▶│  SageMaker TGI  │
│  (EC2)      │     │ (HTTP API)   │     │  (proxy)   │     │    Endpoint     │
└─────────────┘     └──────────────┘     └────────────┘     └─────────────────┘
     ▲                                                              │
     │                                                              │
     └──────────────── Users access via browser ────────────────────┘
```

## Prerequisites

1. **AWS CLI** configured with credentials
2. **VPC with public subnet** (MapPublicIpOnLaunch=true)
3. **GPU quota** for ml.g5.xlarge (check [Service Quotas](../docs/sagemaker_quotas.md))
4. **uv** installed for Lambda packaging ([install](https://github.com/astral-sh/uv))

### Find VPC and Subnet

```bash
# List VPCs
aws ec2 describe-vpcs --region eu-west-1 \
  --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

# List public subnets
aws ec2 describe-subnets --region eu-west-1 \
  --filters Name=vpc-id,Values=vpc-xxx \
  --query 'Subnets[?MapPublicIpOnLaunch==`true`].[SubnetId,AvailabilityZone]' --output table
```

## Deploy Options

| Flag | Default | Description |
|------|---------|-------------|
| `--vpc-id` | (required) | VPC ID |
| `--subnet-id` | (required) | Public subnet ID |
| `--stack-name` | openai-sagemaker-stack | CloudFormation stack name |
| `--model-id` | oriolrius/myemoji-gemma-3-270m-it | HuggingFace model ID |
| `--sagemaker-instance` | ml.g5.xlarge | GPU instance type (must support bfloat16) |
| `--ec2-instance` | t3.small | EC2 instance type |
| `--key-pair` | - | EC2 key pair for SSH |
| `--region` | eu-west-1 | AWS region |
| `--external-sagemaker-role-arn` | - | Use existing SageMaker role (integrated mode) |
| `--lambda-s3-bucket` | auto-created | S3 bucket for Lambda artifacts |

## Outputs

After deployment:
- **OpenWebUI**: `http://<elastic-ip>` (port 80)
- **API Gateway**: `https://xxx.execute-api.region.amazonaws.com`
- **SageMaker Endpoint**: `<stack-name>-vllm-endpoint` (name kept for backwards compatibility)

## Cleanup

```bash
# Delete stack and S3 bucket
./delete-full-stack.sh --stack-name openai-sagemaker-stack

# Keep S3 bucket for faster redeployment
./delete-full-stack.sh --stack-name openai-sagemaker-stack --keep-s3
```

## Cost Estimate

| Resource | Type | Cost |
|----------|------|------|
| SageMaker | ml.g5.xlarge | ~$1.41/hour |
| EC2 | t3.small | ~$0.02/hour |
| API Gateway | HTTP API | ~$1/million requests |
| Lambda | 256MB | Free tier likely covers |
| Elastic IP | Attached | Free |

**Total**: ~$1.45/hour (~$1,044/month if 24/7)

See [sagemaker_quotas.md](../docs/sagemaker_quotas.md) for detailed pricing and GPU specs.

## Files

| File | Description |
|------|-------------|
| `full-stack.yaml` | CloudFormation template |
| `deploy-full-stack.sh` | Deploy script |
| `delete-full-stack.sh` | Cleanup script |
| `STANDALONE.md` | Standalone deployment guide |
| `INTEGRATED.md` | SageMaker Domain integration guide |

## Security Notes

**Development/Testing Only** - This setup has:
- No API authentication on API Gateway
- OpenWebUI with auth disabled
- SSH open (restricted by CIDR parameter)

For production, add:
- API Gateway authentication (API keys, IAM, Cognito)
- OpenWebUI authentication enabled
- VPC endpoints for SageMaker
- HTTPS with custom domain
