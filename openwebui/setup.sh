#!/bin/bash
# OpenWebUI Setup Script
#
# This script installs Docker and starts OpenWebUI.
# Used by CloudFormation EC2 UserData and for local/manual setup.
#
# Usage:
#   # With API Gateway URL
#   OPENAI_API_BASE_URL=https://abc123.execute-api.eu-west-1.amazonaws.com ./setup.sh
#
#   # Or set in .env file
#   ./setup.sh

set -ex

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required variable
if [ -z "$OPENAI_API_BASE_URL" ]; then
    echo "ERROR: OPENAI_API_BASE_URL is required"
    echo "Set it via environment variable or in .env file"
    exit 1
fi

echo "============================================"
echo "OpenWebUI Setup"
echo "============================================"
echo "API URL: $OPENAI_API_BASE_URL"
echo "============================================"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."

    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    fi

    case "$OS" in
        amzn|amazon)
            # Amazon Linux 2023
            dnf update -y
            dnf install -y docker
            ;;
        ubuntu|debian)
            apt-get update
            apt-get install -y docker.io
            ;;
        centos|rhel|fedora)
            dnf install -y docker
            ;;
        *)
            echo "Unsupported OS: $OS"
            echo "Please install Docker manually"
            exit 1
            ;;
    esac

    systemctl enable docker
    systemctl start docker
fi

# Install docker-compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create data directory
mkdir -p data

# Start OpenWebUI
echo "Starting OpenWebUI..."
docker-compose up -d

echo ""
echo "============================================"
echo "OpenWebUI Started!"
echo "============================================"
echo "URL: http://localhost:${OPENWEBUI_PORT:-80}"
echo ""
echo "Logs: docker-compose logs -f"
echo "Stop: docker-compose down"
echo "============================================"
