# OpenWebUI

Web-based chat interface for the SageMaker TGI endpoint.

## Quick Start

### Local Setup

```bash
cd openwebui/

# Copy and configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_BASE_URL to your API Gateway URL

# Run setup (installs Docker if needed)
./setup.sh

# Or manually with docker-compose
docker-compose up -d
```

### Access

- **URL**: http://localhost (or http://localhost:80)
- **Authentication**: Disabled by default

### Configuration

Edit `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_BASE_URL` | API Gateway endpoint URL | Required |
| `OPENAI_API_KEY` | API key (not needed for this setup) | `not-required` |
| `OPENWEBUI_PORT` | Port to expose | `80` |
| `WEBUI_AUTH` | Enable authentication | `false` |

### Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

## Data Persistence

Data is stored in `./data/` directory:
- SQLite database (users, chats, settings)
- Uploaded files

## CloudFormation / Fargate Integration

In production, the CloudFormation template (`infra/full-stack.yaml`) runs OpenWebUI as a **Fargate task** behind an ALB. The container configuration is defined inline in the template (not from these files). These files are for **local development only**.

Fargate container settings: `OPENAI_API_BASE_URL=${HttpApi.ApiEndpoint}/v1`, `WEBUI_AUTH=false`, `ENABLE_OLLAMA_API=false`, 512 CPU / 1024 MB memory.

## Production Notes

For production use:

1. Enable authentication: set `WEBUI_AUTH=true` in the task definition
2. Use HTTPS with a custom domain + ACM certificate on the ALB
3. Add EFS volume for data persistence across Fargate task restarts
