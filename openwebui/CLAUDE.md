# openwebui/

OpenWebUI configuration. Used both for local dev and deployed to EC2 via CloudFormation (S3 -> EC2 UserData).

## Files

- `docker-compose.yml` — runs `ghcr.io/open-webui/open-webui:main` on port 80->8080
- `setup.sh` — installs Docker + docker-compose on EC2/Linux, starts the service
- `.env.example` — template: set `OPENAI_API_BASE_URL` to your API Gateway endpoint

## Local Dev

```bash
cp .env.example .env
# Edit .env with your API Gateway URL
docker-compose up -d
```

## EC2 Deployment

CloudFormation uploads these files to S3, then EC2 UserData downloads and runs `setup.sh` with `OPENAI_API_BASE_URL` set to the API Gateway endpoint.
