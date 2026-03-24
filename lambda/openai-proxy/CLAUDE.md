# lambda/openai-proxy/

OpenAI-compatible API proxy Lambda. Translates OpenAI format to SageMaker TGI invocation.

## Entry Point

`index.lambda_handler` -> re-exports from `openai_proxy/handler.py`.

## Routes (in `handler.py`)

- `GET /v1/models` -> `handle_models_request()`
- `POST /v1/chat/completions` -> `handle_chat_completion()` -> `invoke_sagemaker()`
- `OPTIONS` -> `handle_cors_request()`

## Key Behavior

- `messages_to_prompt()`: joins message contents with newlines
- `invoke_sagemaker()`: sends `{inputs, parameters}` to TGI, strips echoed prompt from output
- Token counts are word-split approximations
- Only dependency: `boto3`. Lazy-initialized SageMaker client.

## Environment Variables

- `SAGEMAKER_ENDPOINT_NAME` — set by CloudFormation
- `AWS_REGION` — defaults to `eu-west-1`

## Dev Commands

```bash
uv sync --dev
uv run pytest -v
uv run ruff check src/ tests/
```

## Packaging

Lambda zip = `boto3` + `src/` contents. Handler: `index.lambda_handler`. Done by `infra/deploy-full-stack.sh`.
