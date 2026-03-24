# Integrated Deployment (SageMaker Domain)

Deploy the TGI endpoint within an existing SageMaker Domain, sharing the execution role with other SageMaker resources like training pipelines and notebooks.

## Prerequisites (Must Already Exist)

This mode **requires** pre-existing SageMaker infrastructure:

| Resource | Required | Created By |
|----------|----------|------------|
| **SageMaker Domain** | Yes | External (e.g., sg-finetune, AWS Console) |
| **SageMaker Execution Role** | Yes | External (same stack as Domain) |
| **VPC and 2 Subnets** | Yes | External or default VPC (2 AZs for ALB) |

### Required Permissions on External Role

The existing SageMaker execution role must have these permissions:

```yaml
# Endpoint management
- sagemaker:CreateModel
- sagemaker:DeleteModel
- sagemaker:DescribeModel
- sagemaker:CreateEndpointConfig
- sagemaker:DeleteEndpointConfig
- sagemaker:DescribeEndpointConfig
- sagemaker:CreateEndpoint
- sagemaker:DeleteEndpoint
- sagemaker:DescribeEndpoint
- sagemaker:UpdateEndpoint
- sagemaker:InvokeEndpoint

# Container access
- ecr:GetAuthorizationToken
- ecr:BatchCheckLayerAvailability
- ecr:GetDownloadUrlForLayer
- ecr:BatchGetImage
```

## What Gets Created vs Reused

| Resource | Created | Reused |
|----------|---------|--------|
| SageMaker Domain | | reused |
| SageMaker Execution Role | | reused |
| SageMaker Model | created | |
| SageMaker Endpoint Config | created | |
| SageMaker Endpoint | created | |
| Lambda Function + Role | created | |
| API Gateway | created | |
| ECS Cluster + Fargate Service | created | |
| ALB + Security Groups | created | |

## Deploy

### Step 1: Get the External Role ARN

```bash
# From CloudFormation stack
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name sg-finetune-sagemaker-domain \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text)

# Or from SageMaker Domain directly
ROLE_ARN=$(aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query 'DefaultUserSettings.ExecutionRole' \
  --output text)

echo $ROLE_ARN
# arn:aws:iam::123456789012:role/sg-finetune-sagemaker-execution-role
```

### Step 2: Get VPC and Subnets from Domain

```bash
# Get Domain's VPC and Subnets (recommended for consistency)
aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query '[VpcId, SubnetIds[0:2]]' \
  --output text
```

### Step 3: Deploy with External Role

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-aaa \
  --subnet-id-2 subnet-bbb \
  --external-sagemaker-role-arn "$ROLE_ARN" \
  --stack-name openai-sagemaker-integrated
```

## When to Use Integrated Mode

- **Unified management** - Single execution role for training + inference
- **SageMaker Studio** - Endpoint visible in Studio UI
- **Existing Domain** - Leverage existing infrastructure
- **Cost tracking** - Consolidated under same role/project

## Verifying Integration

```bash
aws cloudformation describe-stacks \
  --stack-name openai-sagemaker-integrated \
  --query 'Stacks[0].Outputs[?OutputKey==`SageMakerIntegrationMode`].OutputValue' \
  --output text

# Should return: "Integrated (using external SageMaker Domain role)"
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SageMaker Domain (pre-existing)                     │
│                                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐                         │
│  │   SageMaker Studio  │    │  Training Pipeline  │                         │
│  │   (Notebooks, etc)  │    │   (sg-finetune)     │                         │
│  └─────────────────────┘    └─────────────────────┘                         │
│                                       │                                      │
│                                       ▼                                      │
│                          ┌─────────────────────────┐                         │
│                          │  SageMaker Exec Role    │◀────── Shared Role      │
│                          │  (sg-finetune-...-role) │                         │
│                          └───────────┬─────────────┘                         │
│                                      │                                       │
└──────────────────────────────────────┼───────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────────────┐
        │         CloudFormation Stack (this project)                         │
        │                              │                                      │
        │                              ▼                                      │
        │  ┌──────────┐    ┌────────┐    ┌────────┐    ┌─────────────────┐   │
        │  │ OpenWebUI│───▶│  API   │───▶│ Lambda │───▶│  SageMaker TGI  │   │
        │  │(Fargate/ │    │Gateway │    │        │    │    Endpoint     │   │
        │  │   ALB)   │    └────────┘    └────────┘    └─────────────────┘   │
        │  └──────────┘                                        │             │
        │                                              Uses external role     │
        └──────────────────────────────────────────────────────────────────────┘
```

## Cleanup

```bash
./delete-full-stack.sh --stack-name openai-sagemaker-integrated
```

This only deletes resources created by this stack. The SageMaker Domain and execution role remain intact.

## See Also

- [STANDALONE.md](STANDALONE.md) - Deploy without existing Domain
- [README.md](README.md) - Overview and quick start
