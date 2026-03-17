# OpenAI Proxy Lambda

Lambda function that proxies OpenAI-compatible API requests to a SageMaker TGI endpoint.

## Features

- OpenAI-compatible `/v1/chat/completions` endpoint
- OpenAI-compatible `/v1/models` endpoint
- CORS support for browser-based clients
- Converts OpenAI message format to SageMaker TGI format

## Development

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync --dev
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openai_proxy --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_handler.py -v
```

### Lint

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Project Structure

```
lambda/openai-proxy/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── src/
│   ├── index.py            # Lambda entry point
│   └── openai_proxy/
│       ├── __init__.py
│       └── handler.py      # Main handler logic
└── tests/
    └── test_handler.py     # Unit tests
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SAGEMAKER_ENDPOINT_NAME` | SageMaker endpoint name | Required |
| `AWS_REGION` | AWS region | `eu-west-1` |

## Local Testing

```python
from openai_proxy.handler import lambda_handler

event = {
    "requestContext": {"http": {"method": "POST"}},
    "rawPath": "/v1/chat/completions",
    "body": '{"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
}

response = lambda_handler(event, None)
print(response)
```

## Packaging for Lambda

The deployment script (`infra/deploy-full-stack.sh`) handles packaging automatically:

1. Installs dependencies to a temp directory
2. Copies source code
3. Creates zip file
4. Uploads to S3
5. Updates Lambda function

To package manually:

```bash
# Create package directory
mkdir -p dist/package

# Install dependencies
uv pip install --target dist/package boto3

# Copy source
cp -r src/* dist/package/

# Create zip
cd dist/package && zip -r ../lambda.zip . && cd ../..
```
