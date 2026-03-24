# CLAUDE.md

## Rules

1. **Region: `eu-west-1` only.** All AWS CLI commands, deployments, and scripts must target `eu-west-1`. No exceptions.
2. **Never commit credentials.** Use `/aws-credentials-setup` or `/aws-sandbox-credentials` skills.
3. **Use `uv`, never pip.** Three separate `pyproject.toml` files: root, `lambda/openai-proxy/`, `scripts/`.
4. **Run tests before deploying:** `cd lambda/openai-proxy && uv sync --dev && uv run pytest -v`
5. **CloudFormation only.** Never manually create AWS resources.
6. **Always clean up.** Delete stacks when done — SageMaker GPU costs ~$1.41/hr.
7. **Conventional Commits.** Validated by `.githooks/commit-msg` via commitizen. Use `cz commit` or follow format manually.
8. **Ruff** for linting/formatting. Line length 120. Python 3.11+.

## Architecture

```
Browser -> OpenWebUI (Fargate/ALB) -> API Gateway -> Lambda -> SageMaker TGI (ml.g5.xlarge)
```

Single CloudFormation stack (`infra/full-stack.yaml`) deploys everything:
- **SageMaker**: Model + EndpointConfig + Endpoint (HuggingFace TGI, bfloat16, NVIDIA A10G)
- **Lambda**: OpenAI-compatible proxy (`/v1/chat/completions`, `/v1/models`)
- **API Gateway v2**: HTTP API with CORS
- **ECS Fargate**: OpenWebUI container (512 CPU / 1024 MB) behind an ALB
- **IAM**: SageMaker, Lambda, and ECS execution roles

## Key Files

| File | Purpose |
|------|---------|
| `infra/full-stack.yaml` | CloudFormation template — all AWS resources |
| `infra/deploy-full-stack.sh` | Deploy orchestration (packages Lambda, creates S3, deploys CFN) |
| `infra/delete-full-stack.sh` | Stack cleanup |
| `lambda/openai-proxy/src/openai_proxy/handler.py` | Lambda handler — OpenAI format to SageMaker TGI translation |
| `lambda/openai-proxy/src/index.py` | Lambda entry point (re-exports `lambda_handler`) |
| `lambda/openai-proxy/tests/test_handler.py` | Unit tests (moto for AWS mocking) |
| `scripts/src/sagemaker_tools/` | Standalone CLI tools: `deploy_vllm.py`, `test_openai_endpoint.py`, `test_api_gateway.py`, `cleanup.py` |
| `openwebui/` | Docker Compose config + setup script (for local dev; Fargate uses inline config) |
| `.github/workflows/deploy.yml` | CI/CD deploy (40min timeout) |
| `.github/workflows/destroy.yml` | CI/CD destroy (requires typing "DESTROY") |

## CloudFormation Parameters

Required: `VpcId`, `SubnetId`, `SubnetId2` (two public subnets in different AZs for ALB), `LambdaS3Bucket`, `LambdaS3Key`.
Optional: `HuggingFaceModelId` (default: `oriolrius/myemoji-gemma-3-270m-it`), `SageMakerInstanceType` (default: `ml.g5.xlarge`), `ExternalSageMakerRoleArn` (for SageMaker Domain integration with sg-finetune).

## Deploy

```bash
# Credentials
/aws-credentials-setup          # first time
/aws-sandbox-credentials         # refresh expired tokens

# Deploy
cd infra && ./deploy-full-stack.sh \
  --vpc-id vpc-xxx --subnet-id subnet-xxx --subnet-id-2 subnet-yyy

# Test
cd scripts && uv sync && uv run test-endpoint --endpoint-name <name>

# Cleanup
cd infra && ./delete-full-stack.sh --stack-name openai-sagemaker-stack
```

GitHub Actions: secrets need `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`, `VPC_ID`, `SUBNET_ID`, `SUBNET_ID_2`.

## SageMaker GPU Quotas

Gemma 3 requires **bfloat16** — only Ampere+ GPUs (g5: A10G, g6: L4). T4 (g4dn) does NOT work.
See `docs/sagemaker_quotas.md` for full details. Request g5 quota increases via Service Quotas.
