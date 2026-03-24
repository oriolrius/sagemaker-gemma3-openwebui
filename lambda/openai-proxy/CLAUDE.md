# lambda/openai-proxy/

OpenAI-compatible API proxy Lambda. Translates OpenAI format to SageMaker TGI invocation.

## Entry Point

`index.lambda_handler` -> re-exports from `openai_proxy/handler.py`.

## Routes (in `handler.py`)

- `GET /v1/models` -> `handle_models_request()` — returns endpoint name as model
- `POST /v1/chat/completions` -> `handle_chat_completion()` -> `invoke_sagemaker()` -> format as OpenAI response
- `POST /v1/completions` -> same handler
- `OPTIONS` -> `handle_cors_request()`

## Key Behavior

- `messages_to_prompt()`: joins message contents with newlines (simple, no chat template)
- `invoke_sagemaker()`: sends `{inputs, parameters}` to TGI, strips echoed prompt from output
- Token counts are word-split approximations (not tokenizer-based)
- Only dependency: `boto3`. Lazy-initialized SageMaker client for Lambda cold start.

## Environment Variables

- `SAGEMAKER_ENDPOINT_NAME` — set by CloudFormation
- `AWS_REGION` — defaults to `eu-west-1`

## Dev Commands

```bash
uv sync --dev
uv run pytest -v                                    # 19 tests, moto for AWS mocking
uv run pytest --cov=openai_proxy --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Packaging (done by deploy script)

Lambda zip = `boto3` + `src/` contents. Handler path: `index.lambda_handler`.
