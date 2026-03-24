# SageMaker Tools

Python tools for deploying and testing SageMaker TGI endpoints.

> **Note:** The standalone `deploy_vllm.py` script still uses the legacy DJL-LMI/vLLM configuration. For deploying with the current TGI stack, use the CloudFormation deployment (`infra/deploy-full-stack.sh`). The test and cleanup tools work with any SageMaker endpoint.

## Installation

```bash
cd scripts/

# Install with uv (always use uv, not pip)
uv sync
```

## Usage

### Test SageMaker Endpoint

Test the endpoint directly with OpenAI-compatible API:

```bash
# Test specific endpoint
uv run test-endpoint <endpoint-name>

# Auto-detect latest endpoint
uv run test-endpoint
```

### Test API Gateway

Test the API Gateway + Lambda proxy:

```bash
uv run python -m sagemaker_tools.test_api_gateway https://abc123.execute-api.eu-west-1.amazonaws.com
```

### Cleanup Resources

```bash
# Delete specific endpoint
uv run cleanup <endpoint-name>

# List all endpoints
uv run cleanup --list

# Delete all endpoints
uv run cleanup --all
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `eu-west-1` |
| `SAGEMAKER_ENDPOINT_NAME` | Endpoint for testing | Auto-detected |

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/
```

## Scripts

| Script | Description |
|--------|-------------|
| `deploy-vllm` | Deploy standalone SageMaker endpoint (legacy DJL-LMI) |
| `test-endpoint` | Test endpoint with OpenAI API format |
| `cleanup` | Delete SageMaker resources |
