# CLAUDE.md

This document provides guidance for AI agents (Claude Code, Cursor, Copilot, etc.) working with this codebase.

## Project Overview

**sagemaker-using_model** is a complete AWS deployment stack for running HuggingFace language models on SageMaker with an OpenAI-compatible API and web UI.

**Core Components:**
- **SageMaker TGI Endpoint**: GPU-accelerated language model inference using HuggingFace TGI container (bfloat16, NVIDIA A10G)
- **Lambda OpenAI Proxy**: Translates OpenAI API format to SageMaker TGI invocation format
- **API Gateway HTTP API**: Public endpoint with CORS support
- **OpenWebUI on EC2**: Web-based chat interface with Docker
- **CloudFormation IaC**: Single-stack deployment of all resources

## Architecture

![Architecture Diagram](docs/architecture.png)

```
┌──────────────┐     ┌─────────────┐     ┌────────────┐     ┌──────────────────┐
│   Browser    │ ──▶ │  OpenWebUI  │ ──▶ │    API     │ ──▶ │     Lambda       │
│              │     │    (EC2)    │     │  Gateway   │     │  (OpenAI Proxy)  │
└──────────────┘     └─────────────┘     └────────────┘     └──────────────────┘
                                                                     │
                                                                     ▼
                                                            ┌──────────────────┐
                                                            │    SageMaker     │
                                                            │  TGI Endpoint    │
                                                            │ (ml.g5.xlarge)   │
                                                            └──────────────────┘
```

---

## AWS Credentials Setup (CRITICAL)

This project requires valid AWS credentials for deployment. **Never commit credentials to the repository.**

### Claude Code Skills for AWS Credentials

Claude Code provides two specialized skills for managing AWS credentials:

#### 1. `/aws-credentials-setup` - Full Credentials Configuration

**Use this skill to:**
- Configure local AWS CLI credentials (`~/.aws/credentials`)
- Set up GitHub repository secrets for CI/CD workflows
- Integrate with `/aws-sandbox-credentials` for full automation

**When to invoke:**
```
/aws-credentials-setup
```

**Capabilities:**
- Prompts for AWS access key, secret key, and session token
- Validates credentials by calling `aws sts get-caller-identity`
- Writes credentials to the appropriate profile
- Can automatically configure GitHub Actions secrets

#### 2. `/aws-sandbox-credentials` - AWS Innovation Sandbox Automation

**Use this skill when:**
- You need to fetch credentials from AWS Innovation Sandbox portal
- Your session token has expired (sandbox tokens typically expire in 1-4 hours)
- You want to automate the browser-based credential retrieval

**When to invoke:**
```
/aws-sandbox-credentials
```

**Capabilities:**
- Automates browser login with TOTP MFA support
- Navigates to the Innovation Sandbox leases page
- Extracts AWS access keys, secret keys, and session tokens
- Returns credentials for all available roles
- Supports multiple sandbox environments

### Credential Lifecycle Management

| Scenario | Skill to Use | Notes |
|----------|--------------|-------|
| Initial setup (no credentials) | `/aws-credentials-setup` | Configure from scratch |
| Credentials expired | `/aws-sandbox-credentials` | Refresh session tokens |
| GitHub Actions failing | `/aws-credentials-setup` | Update repository secrets |
| New sandbox lease | `/aws-sandbox-credentials` | Fetch new credentials |
| Local development | Either skill | Depends on credential source |

### Environment Variables Required

**For GitHub Actions CI/CD:**
```
AWS_ACCESS_KEY_ID       # IAM access key
AWS_SECRET_ACCESS_KEY   # IAM secret key
AWS_SESSION_TOKEN       # Session token (required for sandbox/STS)
AWS_REGION              # Default: eu-west-1
```

**For Lambda Runtime:**
```
SAGEMAKER_ENDPOINT_NAME # Name of the SageMaker endpoint to invoke
```

### Verifying Credentials

After setting up credentials, always verify:
```bash
aws sts get-caller-identity
aws sagemaker list-endpoints --region eu-west-1
```

---

## Directory Structure

```
sagemaker-using_model/
├── .github/workflows/          # CI/CD automation
│   ├── deploy.yml             # Deploy full stack (40min timeout)
│   └── destroy.yml            # Cleanup with "DESTROY" confirmation
├── infra/                      # Infrastructure as Code
│   ├── full-stack.yaml        # CloudFormation template (23 resources)
│   ├── deploy-full-stack.sh   # Deployment orchestration (316 lines)
│   ├── delete-full-stack.sh   # Cleanup script
│   └── README.md              # Infrastructure documentation
├── lambda/                     # Lambda function
│   └── openai-proxy/          # OpenAI compatibility layer
│       ├── pyproject.toml     # Python project (uv)
│       ├── src/
│       │   ├── index.py       # Entry point (lambda_handler)
│       │   └── openai_proxy/
│       │       └── handler.py # Request handlers (189 lines)
│       └── tests/
│           └── test_handler.py # Unit tests (254 lines)
├── scripts/                    # Standalone deployment tools
│   ├── pyproject.toml         # Python project (uv)
│   └── src/sagemaker_tools/
│       ├── deploy_vllm.py     # Deploy SageMaker endpoint
│       ├── test_openai_endpoint.py  # Test endpoint
│       ├── test_api_gateway.py      # Test API Gateway
│       └── cleanup.py         # Delete resources
├── openwebui/                  # Web UI configuration
│   ├── docker-compose.yml     # Docker Compose config
│   ├── setup.sh               # EC2 setup script (95 lines)
│   └── .env.example           # Configuration template
├── .githooks/                  # Git hooks for commit validation
├── pyproject.toml             # Root project (commitizen config)
├── docs/                      # Additional documentation
│   ├── architecture.drawio   # Architecture diagram (editable)
│   ├── architecture.png      # Architecture diagram (rendered)
│   └── sagemaker_quotas.md   # SageMaker instance quotas and pricing
├── README.md                  # Main documentation
├── cookbook.md                 # Step-by-step deployment cookbook
└── CLAUDE.md                  # This file
```

---

## Key Components Deep Dive

### 1. Lambda OpenAI Proxy (`lambda/openai-proxy/`)

**Purpose:** Translates OpenAI API requests to SageMaker TGI format.

**Entry Point:** `index.lambda_handler` → dispatches to `handler.py`

**Key Functions in `handler.py`:**
| Function | Purpose |
|----------|---------|
| `lambda_handler()` | Main router for HTTP methods |
| `handle_chat_completion()` | Processes `/v1/chat/completions` POST |
| `handle_models_request()` | Returns available models via GET `/v1/models` |
| `invoke_sagemaker()` | Invokes SageMaker endpoint with boto3 |
| `messages_to_prompt()` | Converts OpenAI message format to text |
| `create_chat_completion_response()` | Formats responses as OpenAI-compatible |
| `handle_cors_request()` | Handles CORS preflight OPTIONS |

**Dependencies:** `boto3` only (kept minimal for Lambda)

**Testing:**
```bash
cd lambda/openai-proxy
uv sync --dev
uv run pytest -v
uv run pytest --cov=openai_proxy --cov-report=term-missing
```

### 2. CloudFormation Stack (`infra/full-stack.yaml`)

**Resources Created (23 total):**
- **SageMaker:** Model, EndpointConfig, Endpoint
- **Lambda:** Function, IAM Role, API Gateway Permission
- **API Gateway:** HTTP API, Stage, 5 Routes
- **EC2:** Instance, Security Group, IAM Role/Profile, Elastic IP
- **IAM:** 3 roles with least-privilege policies

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `HuggingFaceModelId` | oriolrius/myemoji-gemma-3-270m-it | Model from HuggingFace Hub |
| `SageMakerInstanceType` | ml.g5.xlarge | GPU instance (must support bfloat16 for Gemma 3) |
| `ExternalSageMakerRoleArn` | (optional) | Existing SageMaker execution role ARN (for Domain integration) |
| `EC2InstanceType` | t3.small | OpenWebUI host |
| `VpcId` | (required) | VPC for deployment |
| `SubnetId` | (required) | Public subnet |
| `EC2KeyPair` | (optional) | SSH access |
| `AllowedSSHCidr` | 0.0.0.0/0 | SSH source CIDR |

**TGI Container Configuration:**
```yaml
HF_MODEL_ID: oriolrius/myemoji-gemma-3-270m-it
SM_NUM_GPUS: '1'
MAX_INPUT_TOKENS: '1024'
MAX_TOTAL_TOKENS: '2048'
DTYPE: bfloat16
MAX_CONCURRENT_REQUESTS: '4'
```

**Container Image:** `huggingface-pytorch-tgi-inference:2.7.0-tgi3.3.6-gpu-py311-cu124-ubuntu22.04-v1.0`

#### SageMaker Domain Integration

This stack supports two deployment modes:

**Mode 1: Standalone (Default)**
- Creates its own SageMaker execution role
- No integration with existing SageMaker Domain
- Use when deploying independently

**Mode 2: Integrated with Existing Domain**
- Uses an existing SageMaker execution role (e.g., from sg-finetune)
- Endpoint appears in the same Domain/Studio environment
- Enables unified management of training + inference

**To deploy with Domain integration:**

```bash
# Get the execution role ARN from the existing Domain stack
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name sg-finetune-sagemaker-domain \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text)

# Deploy with external role
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx \
  --external-sagemaker-role-arn "$ROLE_ARN"
```

**Requirements for integration:**
- The external role must have endpoint management permissions:
  - `sagemaker:CreateModel`, `sagemaker:DeleteModel`, `sagemaker:DescribeModel`
  - `sagemaker:CreateEndpointConfig`, `sagemaker:DeleteEndpointConfig`, `sagemaker:DescribeEndpointConfig`
  - `sagemaker:CreateEndpoint`, `sagemaker:DeleteEndpoint`, `sagemaker:DescribeEndpoint`, `sagemaker:UpdateEndpoint`
  - `sagemaker:InvokeEndpoint`, `sagemaker:InvokeEndpointAsync`
- The role must have ECR access for pulling the TGI container image

**Related project:** [sg-finetune](../sg-finetune/) - SageMaker Domain with training pipeline (same execution role can be shared)

### 3. Deployment Script (`infra/deploy-full-stack.sh`)

**Orchestration Steps:**
1. Parse and validate command-line arguments
2. Package Lambda function with dependencies (boto3)
3. Create S3 bucket for artifacts
4. Upload Lambda ZIP and OpenWebUI files to S3
5. Deploy CloudFormation stack
6. Wait for stack completion (~15-20 minutes)
7. Retrieve and display stack outputs

**Required Arguments:**
- `--vpc-id`: VPC ID (e.g., `vpc-0123456789abcdef0`)
- `--subnet-id`: Public subnet ID

### 4. GitHub Actions Workflows

**`deploy.yml`:**
- Triggers: `workflow_dispatch` with user inputs
- Inputs: stack_name, model_id, sagemaker_instance, ec2_instance
- Timeout: 40 minutes
- Steps: Package Lambda → S3 upload → CloudFormation deploy → Test endpoints

**`destroy.yml`:**
- Requires typing "DESTROY" to confirm
- Validates stack exists before deletion
- Cleans up S3 bucket and CloudFormation stack
- Verifies all resources deleted

---

## Technologies & Conventions

### Technology Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.11+ |
| Package Manager | **uv** (Astral) - NOT pip |
| Cloud | AWS (SageMaker, Lambda, API Gateway, EC2, S3) |
| Infrastructure | CloudFormation YAML |
| CI/CD | GitHub Actions |
| Testing | pytest, moto (AWS mocking) |
| Code Quality | Ruff (linting + formatting) |
| ML Runtime | HuggingFace TGI on SageMaker (bfloat16, CUDA 12.4) |
| Commits | Conventional Commits (Commitizen) |

### Commit Conventions (Conventional Commits)

**Format:**
```
type(scope)?: description

[optional body]

[optional footer(s)]
```

**Version Bumps:**

| Type | Bump | Example |
|------|------|---------|
| `feat` | MINOR | `feat: add streaming support` |
| `fix` | PATCH | `fix: correct Lambda timeout` |
| `feat!` / `fix!` | MAJOR | `feat!: change API response format` |
| `docs`, `style`, `refactor`, `test`, `ci`, `chore` | None | Maintenance |

**Setup:**
```bash
git config core.hooksPath .githooks   # Enable commit validation
uv sync --dev                          # Install commitizen
```

**Usage:**
```bash
git commit -m "feat: add new feature"  # Standard commit (validated)
cz commit                              # Interactive commit
cz bump                                # Bump version based on commits
```

### Code Style

- **Linter/Formatter:** Ruff
- **Line Length:** 120 characters
- **Python Version:** 3.11+ features allowed
- **Style:** PEP 8

---

## Common Tasks

### Deploy Full Stack

```bash
# 1. Ensure AWS credentials are configured
/aws-credentials-setup

# 2. Find your VPC and subnet
aws ec2 describe-vpcs --region eu-west-1 \
  --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

aws ec2 describe-subnets --region eu-west-1 \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query 'Subnets[?MapPublicIpOnLaunch==`true`].[SubnetId,AvailabilityZone]' --output table

# 3. Deploy
cd infra/
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx \
  --ssh-key-name my-key
```

### Deploy via GitHub Actions

1. Ensure repository secrets are configured (`/aws-credentials-setup`)
2. Navigate to Actions → "Deploy Full Stack"
3. Click "Run workflow" with inputs:
   - `stack_name`: CloudFormation stack name
   - `model_id`: HuggingFace model ID
   - `sagemaker_instance`: GPU instance type
   - `ec2_instance`: EC2 instance type

### Test Lambda Locally

```bash
cd lambda/openai-proxy
uv sync --dev
uv run pytest -v
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Test Deployed Endpoint

```bash
cd scripts/
uv sync
uv run test-endpoint --endpoint-name <name>
uv run test-api-gateway --api-url <url>
```

### Cleanup Resources

```bash
# Via script
cd infra/
./delete-full-stack.sh --stack-name openai-sagemaker-stack --region eu-west-1

# Or via GitHub Actions (requires typing "DESTROY")
```

---

## Pre-Flight Checks for Agents

Before making changes, verify:

### 1. AWS Credentials
```bash
aws sts get-caller-identity  # Should return account info
```
If this fails: `/aws-credentials-setup` or `/aws-sandbox-credentials`

### 2. Service Quotas
- Verify GPU quota for `ml.g5.xlarge` in your region (bfloat16 support required for Gemma 3)
- Check: AWS Console → Service Quotas → SageMaker

### 3. VPC/Subnet Readiness
- Subnet must be public (MapPublicIpOnLaunch = true)
- Internet Gateway attached to VPC

### 4. Lambda Tests Pass
```bash
cd lambda/openai-proxy && uv run pytest -v
```

---

## Critical Rules for Agents

1. **AWS Credentials:** Use `/aws-credentials-setup` skill - NEVER commit credentials
2. **Package Manager:** Always use `uv`, never pip directly
3. **Test First:** Run Lambda tests before any deployment
4. **CloudFormation Only:** Never manually create AWS resources
5. **Cleanup Resources:** Always delete stacks when done to avoid costs
6. **Credential Refresh:** Sandbox credentials expire - use `/aws-sandbox-credentials`
7. **Multi-Project:** Lambda and scripts have separate `pyproject.toml` files
8. **GPU Quotas:** Verify SageMaker GPU quota before deployment

---

## File Modification Guide

| File | When to Modify |
|------|----------------|
| `lambda/openai-proxy/src/openai_proxy/handler.py` | Changing OpenAI proxy logic, adding routes |
| `lambda/openai-proxy/tests/test_handler.py` | Adding tests for handler changes |
| `infra/full-stack.yaml` | Adding/modifying AWS resources |
| `infra/deploy-full-stack.sh` | Changing deployment orchestration |
| `scripts/src/sagemaker_tools/` | Changing standalone deployment/test tools |
| `openwebui/docker-compose.yml` | Modifying web UI Docker config |
| `openwebui/setup.sh` | Changing EC2 setup script |
| `.github/workflows/deploy.yml` | Changing CI/CD deploy pipeline |
| `.github/workflows/destroy.yml` | Changing CI/CD cleanup pipeline |
| Root `pyproject.toml` | Changing commitizen config or version |

---

## SageMaker Endpoint Quotas (eu-west-1)

**Full details:** [docs/sagemaker_quotas.md](docs/sagemaker_quotas.md)

**Account:** 658203403846 | **Region:** eu-west-1 | **Total Endpoint Instances:** 20

### Available GPU Instances (Required for TGI)

| Instance Type | Quota | Price/Hour | GPU | GPU Memory | Notes |
|---------------|-------|------------|-----|------------|-------|
| **ml.g5.xlarge** | 0* | ~$1.41 | NVIDIA A10G | 24 GB GDDR6 | **Recommended** - bfloat16 support for Gemma 3 |
| ml.g5.2xlarge | 0* | ~$1.58 | NVIDIA A10G | 24 GB GDDR6 | Larger models |
| ml.g4dn.xlarge | 1 | ~$0.74 | NVIDIA T4 | 16 GB GDDR6 | fp16 only -- NOT for Gemma 3 |
| ml.g4dn.2xlarge | 1 | ~$1.05 | NVIDIA T4 | 16 GB GDDR6 | fp16 only -- NOT for Gemma 3 |

*Request quota increase for g5 instances via Service Quotas.

### Key Points

- **TGI requires GPU** - NVIDIA GPU instances (g4dn, g5, g6 series)
- **Gemma 3 requires bfloat16** - Only Ampere+ GPUs (g5: A10G, g6: L4) support bfloat16; T4 (g4dn) does NOT
- **ARM not supported** - Graviton instances incompatible with TGI GPU container
- **Request increases** - AWS Console → Service Quotas → Amazon SageMaker

See [docs/sagemaker_quotas.md](docs/sagemaker_quotas.md) for complete instance list, pricing, and GPU specifications.

---

## Cost Awareness

| Resource | Type | Cost/Hour | Cost/Month (24/7) |
|----------|------|-----------|-------------------|
| SageMaker | ml.g5.xlarge | ~$1.41 | ~$1,015 |
| EC2 | t3.small | ~$0.02 | ~$14 |
| API Gateway | HTTP API | Pay per request | ~$1/million |
| **Total** | | ~$1.45/hour | ~$1,044/month |

**ALWAYS clean up resources when not in use!**

---

## Troubleshooting

### Deployment Fails
1. Check CloudFormation events in AWS Console for specific error
2. Verify VPC and subnet IDs are correct and in same region
3. Ensure IAM permissions include CloudFormation, SageMaker, Lambda, EC2, S3
4. Check Lambda package builds correctly (no import errors)

### Lambda Timeout
1. Increase timeout in CloudFormation (default: 60s)
2. Check SageMaker endpoint is InService
3. Review CloudWatch logs: `/aws/lambda/<function-name>`
4. Verify endpoint name environment variable is correct

### SageMaker Endpoint Not Responding
1. Check endpoint status: `aws sagemaker describe-endpoint --endpoint-name <name>`
2. Verify model ID is valid HuggingFace model
3. Check instance type has sufficient GPU memory for model
4. Review CloudWatch logs: `/aws/sagemaker/Endpoints/<endpoint-name>`

### AWS Credentials Issues
| Problem | Solution |
|---------|----------|
| Expired credentials | `/aws-sandbox-credentials` to refresh |
| Missing credentials | `/aws-credentials-setup` to configure |
| GitHub Actions failing | Update repository secrets with valid credentials |
| Permission denied | Verify IAM policy allows required actions |
| Invalid token | Session tokens expire - refresh via sandbox |

### OpenWebUI Not Loading
1. Check EC2 security group allows inbound HTTP (port 80)
2. Verify Docker is running: `docker ps` on EC2
3. Check API Gateway URL is configured in OpenWebUI
4. Review Docker logs: `docker-compose logs -f`

### Git Hooks Failing
```bash
git config core.hooksPath .githooks  # Re-enable hooks
cz commit                             # Use interactive commit
```

---

## Quick Reference

### Skills to Remember
- `/aws-credentials-setup` - Configure AWS credentials (local + GitHub)
- `/aws-sandbox-credentials` - Fetch credentials from Innovation Sandbox

### Essential Commands
```bash
# Lambda development
cd lambda/openai-proxy && uv sync --dev && uv run pytest

# Deploy
cd infra && ./deploy-full-stack.sh --vpc-id vpc-xxx --subnet-id subnet-xxx

# Cleanup
cd infra && ./delete-full-stack.sh --stack-name openai-sagemaker-stack

# Commit
cz commit

# Refresh credentials
/aws-sandbox-credentials
```
