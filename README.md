# SageMaker TGI + OpenAI API + OpenWebUI

Deploy a HuggingFace model on AWS SageMaker with HuggingFace TGI (Text Generation Inference), exposed via an OpenAI-compatible API, with OpenWebUI for a chat interface.

## Architecture

![Architecture Diagram](docs/architecture.png)

```
+-----------+     +--------------+     +----------+     +-----------------+
| OpenWebUI |---->| API Gateway  |---->|  Lambda  |---->| SageMaker TGI   |
| (EC2)     |     | (HTTP API)   |     |  (proxy) |     |   Endpoint      |
+-----------+     +--------------+     +----------+     +-----------------+
     ^                    ^
     |                    |
     +-- Browser ---------+-- API Clients (curl, Python, etc.)
```

### Components

| Component | Description |
|-----------|-------------|
| **SageMaker Endpoint** | Runs HuggingFace TGI with your model on GPU (ml.g5.xlarge, NVIDIA A10G) |
| **Lambda** | Proxies OpenAI-format requests to SageMaker TGI format (handles SigV4 signing) |
| **API Gateway** | Public HTTP API (OpenAI-compatible: `/v1/chat/completions`, `/v1/models`) |
| **EC2 + OpenWebUI** | Web-based chat interface |

### Default Model

The default model is **[oriolrius/myemoji-gemma-3-270m-it](https://huggingface.co/oriolrius/myemoji-gemma-3-270m-it)** -- a Gemma 3 270M instruction-tuned model. Being instruction-tuned, it responds naturally to chat-style prompts.

## Quick Start

### Prerequisites

- AWS CLI configured with credentials
- VPC with a public subnet
- GPU quota for ml.g5.xlarge (check Service Quotas)
- [uv](https://github.com/astral-sh/uv) (Python package manager) for Lambda packaging

### Deploy

```bash
cd infra/

# Find your VPC and subnet
aws ec2 describe-vpcs --region eu-west-1 \
  --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

aws ec2 describe-subnets --region eu-west-1 \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query 'Subnets[?MapPublicIpOnLaunch==`true`].[SubnetId,AvailabilityZone]' --output table

# Deploy full stack
./deploy-full-stack.sh \
  --vpc-id vpc-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0
```

Deployment takes ~15-20 minutes (mostly SageMaker endpoint startup).

### Access

After deployment:
- **OpenWebUI**: `http://<ec2-elastic-ip>` (shown in output)
- **API**: `https://<api-id>.execute-api.eu-west-1.amazonaws.com`

### Test API

```bash
# List models
curl https://<api-endpoint>/v1/models

# Chat completion
curl -X POST https://<api-endpoint>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello, how are you?"}], "max_tokens": 50}'
```

### Cleanup

```bash
cd infra/
./delete-full-stack.sh
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model-id` | oriolrius/myemoji-gemma-3-270m-it | HuggingFace model ID |
| `--sagemaker-instance` | ml.g5.xlarge | GPU instance type (must support bfloat16) |
| `--ec2-instance` | t3.small | EC2 instance for OpenWebUI |
| `--key-pair` | - | EC2 key pair for SSH access |
| `--stack-name` | openai-sagemaker-stack | CloudFormation stack name |

### Example: Deploy a different model

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-xxx \
  --subnet-id subnet-xxx \
  --model-id google/gemma-3-1b-it \
  --sagemaker-instance ml.g5.xlarge
```

## Cost

| Resource | Type | Cost |
|----------|------|------|
| SageMaker | ml.g5.xlarge | ~$1.41/hour |
| EC2 | t3.small | ~$0.02/hour |
| API Gateway | HTTP API | ~$1/million requests |

**Total**: ~$1.45/hour (~$1,044/month if 24/7)

**Remember to delete resources when not in use!**

## Inference Runtime

This project uses **HuggingFace TGI** (Text Generation Inference) as the inference runtime on SageMaker:

| Aspect | Value |
|--------|-------|
| Container | `huggingface-pytorch-tgi-inference:2.7.0-tgi3.3.6` |
| Precision | bfloat16 (required for Gemma 3) |
| GPU | NVIDIA A10G (24 GB GDDR6, Ampere) |
| Max input tokens | 1024 |
| Max total tokens | 2048 |

### Why TGI instead of vLLM?

Gemma 3 requires bfloat16 precision and has a specific architecture that TGI supports natively. The HuggingFace TGI container on SageMaker provides:
- Native bfloat16 support on A10G GPUs
- Built-in chat template handling for instruction-tuned models
- Optimized memory management for the Gemma architecture

## Security

This setup is for **development/testing**:
- No API authentication
- OpenWebUI auth disabled

For production, add API Gateway authentication and enable OpenWebUI auth.

## Project Structure

```
.
+-- scripts/                     # SageMaker deployment & testing tools
|   +-- pyproject.toml           # Python project config (uv)
|   +-- src/sagemaker_tools/
|   |   +-- deploy_vllm.py       # Deploy SageMaker endpoint (standalone)
|   |   +-- test_openai_endpoint.py  # Test endpoint directly
|   |   +-- test_api_gateway.py  # Test API Gateway
|   |   +-- cleanup.py           # Delete SageMaker resources
|   +-- README.md
+-- lambda/
|   +-- openai-proxy/            # Lambda function source
|       +-- pyproject.toml       # Python project config (uv)
|       +-- src/
|       |   +-- index.py         # Lambda entry point
|       |   +-- openai_proxy/
|       |       +-- handler.py   # Request handlers (TGI format)
|       +-- tests/
|           +-- test_handler.py  # Unit tests
+-- openwebui/                   # OpenWebUI configuration
|   +-- docker-compose.yml       # Docker Compose config
|   +-- setup.sh                 # Setup script
|   +-- README.md
+-- infra/
|   +-- full-stack.yaml          # CloudFormation template (TGI)
|   +-- deploy-full-stack.sh     # Deployment script
|   +-- delete-full-stack.sh     # Cleanup script
|   +-- README.md
+-- docs/
|   +-- architecture.drawio      # Architecture diagram (editable)
|   +-- architecture.png         # Architecture diagram (rendered)
|   +-- sagemaker_quotas.md      # Instance quotas and pricing
+-- cookbook.md                   # Step-by-step deployment guide
+-- README.md                    # This file
```

## Development

### Lambda Function

```bash
cd lambda/openai-proxy
uv sync --dev

# Run tests
uv run pytest -v

# Lint
uv run ruff check src/ tests/
```

### Scripts (SageMaker Tools)

Standalone Python tools for deploying and testing SageMaker endpoints:

```bash
cd scripts/
uv sync

# Test endpoint directly
uv run test-endpoint <endpoint-name>

# Test API Gateway
uv run python -m sagemaker_tools.test_api_gateway https://abc123.execute-api.eu-west-1.amazonaws.com

# Cleanup
uv run cleanup <endpoint-name>
```

### OpenWebUI (Local)

Run OpenWebUI locally (without CloudFormation):

```bash
cd openwebui/
cp .env.example .env
# Edit .env and set OPENAI_API_BASE_URL

./setup.sh
# Or: docker-compose up -d
```

## License

MIT
