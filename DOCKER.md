# Docker Deployment Guide

This guide explains how to run Dozentenmanager in Docker containers for both development and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Development)](#quick-start-development)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Docker Commands Reference](#docker-commands-reference)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- At least 512MB RAM available
- At least 1GB disk space

## Quick Start (Development)

### 1. Build and run with Docker Compose

```bash
# Build the image and start the container
docker-compose up -d

# View logs
docker-compose logs -f web

# Access the application at http://localhost:5000
```

### 2. Initialize the database

```bash
# Run database migrations
docker-compose exec web alembic upgrade head

# (Optional) Seed with sample data
docker-compose exec web python -c "from cli.university_cli import add_university; add_university('TH Köln')"
```

### 3. Stop the application

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

## Production Deployment

### 1. Prepare environment variables

```bash
# Copy the template
cp .env.docker .env.production

# Edit and set secure values
nano .env.production
```

**CRITICAL**: Set a strong `SECRET_KEY`:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### 2. Build and deploy

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services (with nginx reverse proxy)
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 3. Initialize production database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec web alembic upgrade head

# Create first admin user (if applicable)
docker-compose -f docker-compose.prod.yml exec web python cli/create_admin.py
```

### 4. Access the application

- HTTP: http://your-server-ip:8888
- HTTPS: https://your-domain.com:8443 (configure SSL certificates first)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Environment mode (development/production) |
| `SECRET_KEY` | *required* | Flask secret key for sessions/CSRF |
| `DATABASE_URL` | `sqlite:///instance/dozentenmanager.db` | Database connection string |
| `UPLOAD_FOLDER` | `uploads` | Directory for uploaded files |
| `MAX_CONTENT_LENGTH` | `16777216` | Max upload size (16MB) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Using PostgreSQL (Recommended for Production)

```yaml
# Add to docker-compose.prod.yml
services:
  postgres:
    image: postgres:15-alpine
    container_name: dozentenmanager-db
    environment:
      POSTGRES_DB: dozentenmanager
      POSTGRES_USER: dbuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - dozentenmanager-network
    restart: always

volumes:
  postgres-data:
    driver: local
```

Update `.env.production`:
```
DATABASE_URL=postgresql://dbuser:password@postgres:5432/dozentenmanager
```

### SSL/HTTPS Configuration

1. Obtain SSL certificates (Let's Encrypt recommended):
```bash
# Using certbot
sudo certbot certonly --standalone -d your-domain.com
```

2. Copy certificates:
```bash
mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
```

3. Uncomment HTTPS server block in `nginx.conf`

4. Restart nginx:
```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## Docker Commands Reference

### Build Commands

```bash
# Build development image
docker build -t dozentenmanager:dev .

# Build production image
docker build -t dozentenmanager:prod .

# Build with no cache
docker build --no-cache -t dozentenmanager:latest .
```

### Run Commands

```bash
# Run container directly (without compose)
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  --name dozentenmanager \
  dozentenmanager:latest

# Run with environment file
docker run -d \
  -p 5000:5000 \
  --env-file .env.production \
  dozentenmanager:latest
```

### Management Commands

```bash
# View logs
docker-compose logs -f web
docker logs -f dozentenmanager-prod

# Execute commands in container
docker-compose exec web bash
docker-compose exec web python cli/university_cli.py list

# Restart services
docker-compose restart web
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose stop
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Database Commands

```bash
# Create migration
docker-compose exec web alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec web alembic upgrade head

# Rollback migration
docker-compose exec web alembic downgrade -1

# Check migration status
docker-compose exec web alembic current

# Backup database (SQLite)
docker cp dozentenmanager-prod:/app/instance/dozentenmanager.db ./backup-$(date +%Y%m%d).db

# Restore database (SQLite)
docker cp ./backup.db dozentenmanager-prod:/app/instance/dozentenmanager.db
docker-compose -f docker-compose.prod.yml restart web
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs web

# Check container status
docker-compose ps

# Rebuild image
docker-compose build --no-cache web
docker-compose up -d
```

### Database errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec web alembic upgrade head

# Check database file permissions
docker-compose exec web ls -la instance/
```

### Permission denied errors

```bash
# Fix volume permissions
docker-compose exec web chown -R appuser:appuser /app/instance /app/uploads
```

### Port already in use

```bash
# Change port in docker-compose.yml
ports:
  - "8080:5000"  # Use port 8080 instead

# Or stop conflicting service
sudo lsof -ti:5000 | xargs kill -9
```

### Health check failing

```bash
# Install requests in container (if missing)
docker-compose exec web pip install requests

# Or disable health check in Dockerfile/docker-compose.yml
```

### Out of disk space

```bash
# Clean up Docker system
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Check disk usage
docker system df
```

## Performance Tuning

### Resource Limits

Edit `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Increase CPU limit
      memory: 1024M    # Increase memory limit
    reservations:
      cpus: '1.0'
      memory: 512M
```

### Worker Configuration

For production with Gunicorn (recommended):

1. Install Gunicorn:
```bash
# Add to pyproject.toml dependencies
gunicorn>=21.2.0
```

2. Update Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "run:app"]
```

### Monitoring

```bash
# Monitor container stats
docker stats dozentenmanager-prod

# Monitor logs in real-time
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## Security Best Practices

1. ✅ Always use a strong, random `SECRET_KEY`
2. ✅ Never commit `.env` files to version control
3. ✅ Use HTTPS in production (configure SSL)
4. ✅ Keep base images updated (`docker pull python:3.12-slim`)
5. ✅ Use non-root user (already configured)
6. ✅ Enable Docker Content Trust (`export DOCKER_CONTENT_TRUST=1`)
7. ✅ Scan images for vulnerabilities (`docker scan dozentenmanager:latest`)
8. ✅ Use secrets management (Docker Swarm secrets, Kubernetes secrets, etc.)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)
- [Nginx Documentation](https://nginx.org/en/docs/)
