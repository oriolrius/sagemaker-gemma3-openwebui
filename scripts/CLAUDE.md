# scripts/

Standalone CLI tools for deploying and testing SageMaker endpoints outside CloudFormation.

## CLI Entry Points

- `deploy-vllm` -> `sagemaker_tools.deploy_vllm:main`
- `test-endpoint` -> `sagemaker_tools.test_openai_endpoint:main`
- `cleanup` -> `sagemaker_tools.cleanup:main`

## Usage

```bash
uv sync
uv run test-endpoint --endpoint-name <name>
uv run cleanup
```

Separate `pyproject.toml` from root and lambda. Dependencies: `boto3`.
