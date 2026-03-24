# CLAUDE.md

## Rules

1. **Region: `eu-west-1` only.** All AWS commands and deployments must target `eu-west-1`.
2. **Never commit credentials.** Use `/aws-credentials-setup` or `/aws-sandbox-credentials` skills.
3. **Use `uv`, never pip.** Three separate `pyproject.toml`: root, `lambda/openai-proxy/`, `scripts/`.
4. **Run tests before deploying:** `cd lambda/openai-proxy && uv sync --dev && uv run pytest -v`
5. **CloudFormation only.** Never manually create AWS resources.
6. **Always clean up.** SageMaker GPU costs ~$1.41/hr.
7. **Conventional Commits** validated by `.githooks/commit-msg` via commitizen.
8. **Ruff** for linting/formatting. Line length 120. Python 3.11+.

## Architecture

```
Browser -> OpenWebUI (Fargate/ALB) -> API Gateway -> Lambda -> SageMaker TGI (ml.g5.xlarge)
```

Single CloudFormation stack (`infra/full-stack.yaml`) deploys 23 resources: SageMaker (TGI bfloat16), Lambda (OpenAI proxy), API Gateway v2, ECS Fargate (OpenWebUI + ALB), and IAM roles.

Gemma 3 requires **bfloat16** — only Ampere+ GPUs (g5: A10G). T4/g4dn does NOT work. See `docs/sagemaker_quotas.md`.
