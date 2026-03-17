# Integrated Deployment (SageMaker Domain)

Deploy the TGI endpoint within an existing SageMaker Domain, sharing the execution role with other SageMaker resources like training pipelines and notebooks.

## Prerequisites (Must Already Exist)

This mode **requires** pre-existing SageMaker infrastructure:

| Resource | Required | Created By |
|----------|----------|------------|
| **SageMaker Domain** | Yes | External (e.g., sg-finetune, AWS Console) |
| **SageMaker Execution Role** | Yes | External (same stack as Domain) |
| **VPC and Subnets** | Yes | External or default VPC |

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
| SageMaker Domain | | ✅ |
| SageMaker Execution Role | | ✅ |
| SageMaker Model | ✅ | |
| SageMaker Endpoint Config | ✅ | |
| SageMaker Endpoint | ✅ | |
| Lambda Function + Role | ✅ | |
| API Gateway | ✅ | |
| EC2 + Security Group | ✅ | |

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

### Step 2: Get VPC and Subnet from Domain

```bash
# Get Domain's VPC and Subnets (recommended for consistency)
aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query '[VpcId, SubnetIds[0]]' \
  --output text
```

### Step 3: Deploy with External Role

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0 \
  --external-sagemaker-role-arn "$ROLE_ARN" \
  --stack-name openai-sagemaker-integrated
```

## When to Use Integrated Mode

- **Unified management** - Single execution role for training + inference
- **SageMaker Studio** - Endpoint visible in Studio UI
- **Existing Domain** - Leverage existing infrastructure
- **Cost tracking** - Consolidated under same role/project
- **Team environments** - Shared SageMaker Domain

## Example: Integration with sg-finetune

The [sg-finetune](https://github.com/oriolrius/sg-finetune) project provides a SageMaker Domain with training pipelines. To deploy inference alongside it:

```bash
# Get role from sg-finetune stack
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name sg-finetune-sagemaker-domain \
  --region eu-west-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text)

# Deploy integrated
./deploy-full-stack.sh \
  --vpc-id vpc-0496b1fd0ee93bda5 \
  --subnet-id subnet-0be946f5bcf8899a1 \
  --external-sagemaker-role-arn "$ROLE_ARN" \
  --stack-name openai-sagemaker-integrated \
  --region eu-west-1
```

## Verifying Integration

After deployment, check the outputs:

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
        │  │  (EC2)   │    │Gateway │    │        │    │    Endpoint     │   │
        │  └──────────┘    └────────┘    └────────┘    └─────────────────┘   │
        │                                                       │             │
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
