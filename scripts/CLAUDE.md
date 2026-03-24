# scripts/

Standalone CLI tools for deploying and testing SageMaker endpoints outside CloudFormation.

## CLI Entry Points (from `pyproject.toml`)

- `deploy-vllm` -> `sagemaker_tools.deploy_vllm:main` — deploy SageMaker endpoint directly
- `test-endpoint` -> `sagemaker_tools.test_openai_endpoint:main` — test deployed endpoint
- `cleanup` -> `sagemaker_tools.cleanup:main` — delete SageMaker resources

## Usage

```bash
uv sync
uv run test-endpoint --endpoint-name <name>
uv run deploy-vllm
uv run cleanup
```

Separate `pyproject.toml` from root and lambda. Dependencies: `boto3`. Dev: `pytest`, `moto`, `ruff`.
