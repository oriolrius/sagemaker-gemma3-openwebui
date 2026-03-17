# Standalone Deployment

Deploy the full stack as an independent, self-contained environment. This mode creates all required resources including its own SageMaker execution role.

## What Gets Created

| Resource | Description |
|----------|-------------|
| **SageMaker Execution Role** | New IAM role with SageMaker and ECR permissions |
| **SageMaker Model** | TGI model configuration |
| **SageMaker Endpoint Config** | Endpoint configuration with instance type |
| **SageMaker Endpoint** | Real-time inference endpoint |
| **Lambda Function** | OpenAI API proxy |
| **Lambda Execution Role** | IAM role for Lambda |
| **API Gateway HTTP API** | Public API endpoint |
| **EC2 Instance** | OpenWebUI host |
| **EC2 Security Group** | Network rules for EC2 |
| **EC2 IAM Role** | Instance profile for S3 access |
| **Elastic IP** | Static public IP |

## Prerequisites

1. **AWS CLI** configured with credentials
2. **VPC with public subnet** (MapPublicIpOnLaunch=true)
3. **GPU quota** for ml.g5.xlarge (check Service Quotas)
4. **uv** installed for Lambda packaging

## Deploy

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0
```

### Optional Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--stack-name` | openai-sagemaker-stack | CloudFormation stack name |
| `--model-id` | oriolrius/myemoji-gemma-3-270m-it | HuggingFace model ID |
| `--sagemaker-instance` | ml.g5.xlarge | GPU instance type (must support bfloat16) |
| `--ec2-instance` | t3.small | EC2 instance type |
| `--key-pair` | - | EC2 key pair for SSH |
| `--region` | eu-west-1 | AWS region |

## When to Use Standalone Mode

- **Quick testing** - No existing SageMaker infrastructure
- **Isolated environments** - Separate from other projects
- **Simple deployments** - No need to share resources
- **Development** - Independent experimentation

## Cleanup

```bash
./delete-full-stack.sh --stack-name openai-sagemaker-stack
```

This deletes all resources including the SageMaker execution role.

## Architecture

```
                     ┌─────────────────────────────────────────────────────────┐
                     │              CloudFormation Stack                       │
                     │                                                         │
┌─────────┐         │  ┌──────────┐    ┌────────┐    ┌─────────────────────┐  │
│ Browser │─────────┼─▶│ OpenWebUI│───▶│  API   │───▶│      Lambda         │  │
└─────────┘         │  │  (EC2)   │    │Gateway │    │   (OpenAI Proxy)    │  │
                     │  └──────────┘    └────────┘    └──────────┬──────────┘  │
                     │                                           │             │
                     │                                           ▼             │
                     │                               ┌─────────────────────┐   │
                     │                               │  SageMaker Endpoint │   │
                     │                               │  (TGI + Gemma 3)    │   │
                     │                               └─────────────────────┘   │
                     │                                           │             │
                     │                                           ▼             │
                     │                               ┌─────────────────────┐   │
                     │                               │ SageMaker Exec Role │   │
                     │                               │   (created by CF)   │   │
                     │                               └─────────────────────┘   │
                     └─────────────────────────────────────────────────────────┘
```

## See Also

- [INTEGRATED.md](INTEGRATED.md) - Deploy within existing SageMaker Domain
- [README.md](README.md) - Overview and quick start
