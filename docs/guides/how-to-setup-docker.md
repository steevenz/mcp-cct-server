# Guide: Docker Setup for CCT MCP Server

This guide provides comprehensive instructions for running the CCT MCP Server using Docker, including single-container deployment, Docker Compose for multi-container setups, and production configurations.

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Configuration](#3-configuration)
4. [Docker Compose](#4-docker-compose)
5. [Production Deployment](#5-production-deployment)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Prerequisites

- **Docker** installed (version 20.10 or higher recommended)
- **Docker Compose** installed (for multi-container setups)
- At least **2GB RAM** available for Docker
- **API key** for your preferred LLM provider (optional but recommended)

### Install Docker

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**macOS:**
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

**Windows:**
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

---

## 2. Quick Start

### Build and Run

```bash
# Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Build the Docker image
docker build -t cct-mcp-server:latest .

# Run the container
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  -e CCT_LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY=your_api_key_here \
  cct-mcp-server:latest
```

### Verify Installation

```bash
# Check container status
docker ps | grep cct-server

# Check logs
docker logs cct-server

# Test health endpoint
curl http://localhost:8000/health
```

---

## 3. Configuration

### Environment Variables

The Docker image uses the same environment variables as the standard setup. Configure them using:

**1. Environment file (.env):**
```bash
# Create .env file
cp .env.example .env

# Edit with your configuration
nano .env
```

**2. Docker run flags:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  -e CCT_HOST=0.0.0.0 \
  -e CCT_PORT=8000 \
  -e CCT_TRANSPORT=sse \
  -e CCT_LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY=your_api_key \
  cct-mcp-server:latest
```

### Volume Mounting

**Database Persistence:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  cct-mcp-server:latest
```

**Configuration Files:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/.env:/app/.env \
  cct-mcp-server:latest
```

### Port Mapping

```bash
# Default port 8000
docker run -d -p 8000:8000 cct-mcp-server:latest

# Custom port 8001
docker run -d -p 8001:8000 -e CCT_PORT=8001 cct-mcp-server:latest

# Multiple ports (if needed)
docker run -d -p 8000:8000 -p 8001:8001 cct-mcp-server:latest
```

---

## 4. Docker Compose

### Basic Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    container_name: cct-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
      - ./.env:/app/.env
    environment:
      - CCT_HOST=0.0.0.0
      - CCT_PORT=8000
      - CCT_TRANSPORT=sse
      - CCT_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sqlite3; conn = sqlite3.connect('/app/database/cct_memory.db'); conn.execute('SELECT 1'); conn.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

**Run with Docker Compose:**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Multi-Agent Setup with Docker Compose

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    container_name: cct-multi-agent-server
    ports:
      - "8001:8001"
    volumes:
      - ./database:/app/database
      - ./.env:/app/.env
    environment:
      - CCT_HOST=0.0.0.0
      - CCT_PORT=8001
      - CCT_TRANSPORT=sse
      - CCT_MAX_SESSIONS=500
      - CCT_LOG_LEVEL=INFO
    restart: unless-stopped
```

**Run multi-agent server:**
```bash
docker-compose up -d

# Connect multiple IDEs to http://localhost:8001
```

### Docker Compose with Environment File

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    container_name: cct-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
    env_file:
      - .env
    restart: unless-stopped
```

---

## 5. Production Deployment

### Production Docker Compose

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    container_name: cct-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    env_file:
      - .env.production
    environment:
      - CCT_LOG_LEVEL=WARNING
      - CCT_MAX_SESSIONS=500
    restart: always
    healthcheck:
      test: ["CMD", "python", "-c", "import sqlite3; conn = sqlite3.connect('/app/database/cct_memory.db'); conn.execute('SELECT 1'); conn.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Resource Limits

```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  --memory="2g" \
  --cpus="1.5" \
  --restart=always \
  cct-mcp-server:latest
```

### Security Best Practices

**1. Run as non-root user:**
```dockerfile
# Add to Dockerfile before CMD
RUN useradd -m -u 1000 cctuser
USER cctuser
```

**2. Use read-only root filesystem:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd)/database:/app/database \
  cct-mcp-server:latest
```

**3. Limit capabilities:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  cct-mcp-server:latest
```

### Docker Registry

**Push to Docker Hub:**
```bash
# Tag image
docker tag cct-mcp-server:latest yourusername/cct-mcp-server:latest

# Login to Docker Hub
docker login

# Push image
docker push yourusername/cct-mcp-server:latest
```

**Pull and run from registry:**
```bash
docker pull yourusername/cct-mcp-server:latest
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  -v $(pwd)/database:/app/database \
  yourusername/cct-mcp-server:latest
```

---

## 6. Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs cct-server
```

**Check if port is in use:**
```bash
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

**Check container status:**
```bash
docker ps -a | grep cct-server
```

### Database Issues

**Database not persisting:**
```bash
# Ensure volume is mounted correctly
docker inspect cct-server | grep Mounts

# Check database directory permissions
ls -la database/
```

**Database locked:**
```bash
# Stop container
docker stop cct-server

# Remove lock file (if exists)
rm database/cct_memory.db-shm
rm database/cct_memory.db-wal

# Restart container
docker start cct-server
```

### Memory Issues

**Check container resource usage:**
```bash
docker stats cct-server
```

**Increase memory limit:**
```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  --memory="4g" \
  cct-mcp-server:latest
```

### Network Issues

**Container can't access external APIs:**
```bash
# Check container DNS
docker run --rm cct-mcp-server cat /etc/resolv.conf

# Use host network (for testing only)
docker run -d \
  --name cct-server \
  --network=host \
  cct-mcp-server:latest
```

### Health Check Failures

**Check health check status:**
```bash
docker inspect cct-server | grep Health
```

**Disable health check temporarily:**
```bash
docker run -d \
  --name cct-server \
  --no-healthcheck \
  cct-mcp-server:latest
```

### Rebuild Image

```bash
# Remove old image
docker rmi cct-mcp-server:latest

# Rebuild without cache
docker build --no-cache -t cct-mcp-server:latest .

# Rebuild with Docker Compose
docker-compose build --no-cache
docker-compose up -d
```

---

## Advanced Usage

### Custom Entrypoint

```bash
docker run -d \
  --name cct-server \
  -p 8000:8000 \
  --entrypoint ["python", "-m", "src.main", "--transport", "sse"] \
  cct-mcp-server:latest
```

### Multi-Container Setup

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    container_name: cct-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
    environment:
      - CCT_TRANSPORT=sse
    networks:
      - cct-network

  # Add other services as needed
  # nginx:
  #   image: nginx:alpine
  #   ports:
  #     - "80:80"
  #   volumes:
  #     - ./nginx.conf:/etc/nginx/nginx.conf

networks:
  cct-network:
    driver: bridge
```

### Docker Swarm Deployment

```yaml
version: '3.8'

services:
  cct-server:
    image: cct-mcp-server:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    ports:
      - "8000:8000"
    volumes:
      - cct-data:/app/database
    environment:
      - CCT_TRANSPORT=sse
      - CCT_MAX_SESSIONS=500

volumes:
  cct-data:
```

**Deploy to Swarm:**
```bash
docker stack deploy -c docker-compose.yml cct-stack
```

---

## Summary

**Key Points:**
- Docker provides consistent deployment across platforms
- Use volume mounts for database persistence
- Configure environment variables for LLM providers
- Use Docker Compose for multi-container setups
- Implement health checks for production monitoring
- Set resource limits for production deployments
- Follow security best practices for production

**Quick Commands:**
```bash
# Build
docker build -t cct-mcp-server:latest .

# Run
docker run -d -p 8000:8000 -v $(pwd)/database:/app/database cct-mcp-server:latest

# Compose
docker-compose up -d

# Logs
docker logs -f cct-server
docker-compose logs -f

# Stop
docker stop cct-server
docker-compose down
```

**Getting Help:**
- Check container logs for errors
- Verify volume mounts are correct
- Ensure environment variables are set
- Check network connectivity
- Review Docker documentation for advanced configurations
