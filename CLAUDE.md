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

## Releases

Use **commitizen** for version bumps and **`gh` CLI** (GitHub account: `oriolrius`) for releases.

### Version Bump + Release Process

```bash
# 1. Bump version (updates all 3 pyproject.toml + creates git tag)
uvx --from commitizen cz bump              # auto-detects bump type from commits (feat=MINOR, fix=PATCH, feat!=MAJOR)
# or force a specific bump:
uvx --from commitizen cz bump --increment MAJOR   # for breaking changes
uvx --from commitizen cz bump --increment MINOR   # for new features
uvx --from commitizen cz bump --increment PATCH   # for bug fixes

# 2. Push commits + tag
git push origin main --tags

# 3. Create GitHub release from the tag
gh release create v<version> --generate-notes
```

### Commitizen Config (root `pyproject.toml`)

- `tag_format`: `v$version` (e.g., `v2.0.0`)
- `version_files`: syncs version across `pyproject.toml`, `lambda/openai-proxy/pyproject.toml`, `scripts/pyproject.toml`
- `major_version_zero`: `false` (breaking changes bump MAJOR)

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Active development (currently v2.x, Fargate) |
| `v1.x` | Maintenance branch for EC2 architecture (v1.0.0) |
| `v2.x` | Maintenance branch for Fargate architecture (v2.0.0) |
