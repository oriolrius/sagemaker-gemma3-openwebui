# Infrastructure

CloudFormation template for deploying a SageMaker TGI endpoint with OpenAI-compatible API and OpenWebUI on EC2.

## Quick Start

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx
```

## Architecture

See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for full architecture description and diagram.

```
+-----------+     +--------------+     +----------+     +-----------------+
| OpenWebUI |---->| API Gateway  |---->|  Lambda  |---->| SageMaker TGI   |
| (EC2)     |     | (HTTP API)   |     |  (proxy) |     |   Endpoint      |
+-----------+     +--------------+     +----------+     +-----------------+
```

## Prerequisites

1. **AWS CLI** configured with credentials
2. **VPC with public subnet** (MapPublicIpOnLaunch=true)
3. **GPU quota** for ml.g5.xlarge (check [Service Quotas](../docs/sagemaker_quotas.md))
4. **uv** installed for Lambda packaging

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
| `--lambda-s3-bucket` | auto-created | S3 bucket for Lambda artifacts |

## Outputs

After deployment:
- **OpenWebUI**: `http://<elastic-ip>` (port 80)
- **API Gateway**: `https://xxx.execute-api.eu-west-1.amazonaws.com`
- **SageMaker Endpoint**: `<stack-name>-vllm-endpoint`

## Cleanup

```bash
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

**Total**: ~$1.45/hour (~$1,044/month if 24/7)

## Files

| File | Description |
|------|-------------|
| `full-stack.yaml` | CloudFormation template |
| `deploy-full-stack.sh` | Deploy script |
| `delete-full-stack.sh` | Cleanup script |

## Security Notes

**Development/Testing Only** - No API authentication, OpenWebUI auth disabled, SSH open (restricted by CIDR). For production, add API Gateway auth, enable OpenWebUI auth, HTTPS with custom domain.
