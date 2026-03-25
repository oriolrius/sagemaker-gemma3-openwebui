# Infrastructure

CloudFormation template for deploying a SageMaker TGI endpoint with OpenAI-compatible API and OpenWebUI on Fargate.

## Quick Start

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-aaa \
  --subnet-id-2 subnet-bbb
```

## Architecture

See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for full architecture description and diagram.

```
+--------------+     +--------------+     +----------+     +-----------------+
|  OpenWebUI   |---->| API Gateway  |---->|  Lambda  |---->| SageMaker TGI   |
| (Fargate/ALB)|     | (HTTP API)   |     |  (proxy) |     |    Endpoint     |
+--------------+     +--------------+     +----------+     +-----------------+
```

## Prerequisites

1. **AWS CLI** configured with credentials
2. **VPC with 2 public subnets** in different AZs (required for ALB)
3. **GPU quota** for ml.g5.xlarge (check [Service Quotas](../docs/sagemaker_quotas.md))
4. **uv** installed for Lambda packaging

## Deploy Options

| Flag | Default | Description |
|------|---------|-------------|
| `--vpc-id` | (required) | VPC ID |
| `--subnet-id` | (required) | First public subnet |
| `--subnet-id-2` | (required) | Second public subnet (different AZ, for ALB) |
| `--stack-name` | openai-sagemaker-stack | CloudFormation stack name |
| `--model-id` | oriolrius/myemoji-gemma-3-270m-it | HuggingFace model ID |
| `--sagemaker-instance` | ml.g5.xlarge | GPU instance type (must support bfloat16) |
| `--region` | eu-west-1 | AWS region |
| `--lambda-s3-bucket` | auto-created | S3 bucket for Lambda artifacts |

## Outputs

After deployment:
- **OpenWebUI**: `http://<alb-dns-name>` (port 80)
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
| Fargate | 0.5 vCPU / 1 GB | ~$0.03/hour |
| ALB | Application LB | ~$0.02/hour |
| API Gateway | HTTP API | ~$1/million requests |

**Total**: ~$1.46/hour (~$1,051/month if 24/7)

## Files

| File | Description |
|------|-------------|
| `full-stack.yaml` | CloudFormation template (23 resources) |
| `deploy-full-stack.sh` | Deploy script |
| `delete-full-stack.sh` | Cleanup script |

## Security Notes

**Development/Testing Only** - No API authentication, OpenWebUI auth disabled. For production, add API Gateway authentication and enable OpenWebUI auth.
