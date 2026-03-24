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
| **ECS Cluster** | Fargate orchestration |
| **ECS Task Definition** | OpenWebUI container config (0.5 vCPU / 1 GB) |
| **ECS Service** | Manages Fargate tasks |
| **Application Load Balancer** | Internet-facing, port 80, 2 AZs |
| **ALB Target Group** | Routes to Fargate tasks on port 8080 |
| **ALB Security Group** | Allows inbound HTTP (port 80) |
| **Fargate Security Group** | Allows port 8080 from ALB only |
| **ECS Task Execution Role** | ECR pull + CloudWatch Logs |
| **CloudWatch Log Group** | `/ecs/<stack>/openwebui`, 7-day retention |

## Prerequisites

1. **AWS CLI** configured with credentials
2. **VPC with 2 public subnets** in different AZs (required for ALB)
3. **GPU quota** for ml.g5.xlarge (check Service Quotas)
4. **uv** installed for Lambda packaging

## Deploy

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-aaa \
  --subnet-id-2 subnet-bbb
```

### Optional Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--stack-name` | openai-sagemaker-stack | CloudFormation stack name |
| `--model-id` | oriolrius/myemoji-gemma-3-270m-it | HuggingFace model ID |
| `--sagemaker-instance` | ml.g5.xlarge | GPU instance type (must support bfloat16) |
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
└─────────┘         │  │(Fargate/ │    │Gateway │    │   (OpenAI Proxy)    │  │
                     │  │   ALB)   │    └────────┘    └──────────┬──────────┘  │
                     │  └──────────┘                             │             │
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
