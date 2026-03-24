# openwebui/

Local development files for OpenWebUI. **In production, Fargate uses inline config from `infra/full-stack.yaml` — these files are not deployed.**

## Files

- `docker-compose.yml` — runs `ghcr.io/open-webui/open-webui:main` on port 80->8080
- `setup.sh` — installs Docker + docker-compose on a fresh Linux box, starts the service
- `.env.example` — template: set `OPENAI_API_BASE_URL` to your API Gateway endpoint

## Local Dev

```bash
cp .env.example .env
# Edit .env with your API Gateway URL
docker-compose up -d
# Open http://localhost
```

## Fargate Equivalent

The CloudFormation template configures the same container with: `OPENAI_API_BASE_URL=${HttpApi.ApiEndpoint}/v1`, `WEBUI_AUTH=false`, `ENABLE_OLLAMA_API=false`.
