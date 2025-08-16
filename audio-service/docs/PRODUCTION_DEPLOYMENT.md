# Production Deployment Guide

## Overview

This guide covers the production deployment of the Tempo Processing API, including infrastructure requirements, security considerations, monitoring, and scaling strategies.

## Infrastructure Requirements

### Hardware Requirements

**Minimum Production Specifications:**
- **CPU**: 8+ cores (16+ recommended for high-volume)
- **RAM**: 16GB+ (32GB+ recommended for concurrent processing)
- **Storage**: 500GB+ SSD for cache and temporary files
- **Network**: 1Gbps+ for file transfers

**Recommended Production Setup:**
- **CPU**: 16-32 cores with high single-thread performance
- **RAM**: 64GB+ for optimal caching and concurrent processing
- **Storage**: 2TB+ NVMe SSD with high IOPS
- **Network**: 10Gbps for high-volume deployments

### Software Dependencies

**Core Dependencies:**
```bash
# Python 3.10+
python3.10 --version

# Redis for caching and rate limiting
redis-server --version  # 6.0+

# FFmpeg for audio processing
ffmpeg -version  # 4.4+

# PostgreSQL/MySQL for job tracking (optional)
psql --version  # 13+
```

**Python Packages:**
```bash
pip install -r requirements.txt
pip install -r requirements-production.txt
```

### Container Deployment (Docker)

**Dockerfile.production:**
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash beatforge
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .
RUN chown -R beatforge:beatforge /app

# Switch to non-root user
USER beatforge

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
```

**docker-compose.production.yml:**
```yaml
version: '3.8'

services:
  tempo-api:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379
      - STORAGE_TYPE=r2
      - LOG_LEVEL=INFO
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    depends_on:
      - redis
      - celery-worker
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.production
    command: ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4"]
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379
      - STORAGE_TYPE=r2
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "celery", "-A", "celery_app", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tempo-api
    restart: unless-stopped

volumes:
  redis_data:
```

## Configuration Management

### Environment Variables

**Production Environment File (.env.production):**
```bash
# Environment
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4

# Security
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/beatforge

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_RATE_LIMIT_DB=1
REDIS_CACHE_DB=2

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT=1500  # 25 minutes

# Storage Configuration (R2/CloudFlare)
STORAGE_TYPE=r2
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_BUCKET=your-bucket-name
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com

# Rate Limiting
RATE_LIMIT_STORAGE=redis://redis:6379/1
ENABLE_RATE_LIMITING=true
RATE_LIMIT_STRATEGY=sliding_window

# Performance
CACHE_TTL_SECONDS=3600
MAX_CACHE_SIZE_MB=1000
ENABLE_PERFORMANCE_MONITORING=true

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
ENABLE_METRICS=true

# Feature Flags
ENABLE_TEMPO_PROCESSING=true
ENABLE_ADVANCED_FEATURES=true
ENABLE_BETA_FEATURES=false
```

### Production Configuration Files

**gunicorn.conf.py:**
```python
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('API_PORT', 8001)}"
backlog = 2048

# Worker processes
workers = int(os.getenv('API_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'beatforge-tempo-api'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
worker_tmp_dir = '/dev/shm'
```

**nginx.conf:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream tempo_api {
        server tempo-api:8001;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=uploads:10m rate=2r/s;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    server {
        listen 80;
        server_name api.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        client_max_body_size 100M;
        client_body_timeout 60s;
        client_header_timeout 60s;

        # API endpoints
        location /tempo/ {
            limit_req zone=uploads burst=5 nodelay;
            proxy_pass http://tempo_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 180s;
            proxy_send_timeout 180s;
        }

        location / {
            limit_req zone=api burst=10 nodelay;
            proxy_pass http://tempo_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint (no rate limiting)
        location /health {
            proxy_pass http://tempo_api;
            access_log off;
        }
    }
}
```

## Security Configuration

### SSL/TLS Setup

**SSL Certificate Installation:**
```bash
# Using Let's Encrypt with Certbot
apt-get install certbot python3-certbot-nginx
certbot --nginx -d api.yourdomain.com

# Manual certificate installation
mkdir -p /etc/nginx/ssl
cp your-certificate.crt /etc/nginx/ssl/cert.pem
cp your-private-key.key /etc/nginx/ssl/key.pem
chmod 600 /etc/nginx/ssl/key.pem
```

### API Authentication

**Production API Key Management:**
```python
# config/security.py
import secrets
import hashlib
from typing import Optional

class APIKeyManager:
    def __init__(self):
        self.valid_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> dict:
        """Load API keys from secure storage"""
        # In production, load from environment or secure key management
        return {
            "client_1": {
                "key_hash": "sha256_hash_of_key",
                "permissions": ["tempo:read", "tempo:write"],
                "rate_limit_tier": "premium"
            }
        }
    
    def validate_key(self, api_key: str) -> Optional[dict]:
        """Validate API key and return client info"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        for client_id, client_info in self.valid_keys.items():
            if client_info["key_hash"] == key_hash:
                return {
                    "client_id": client_id,
                    **client_info
                }
        return None

    def generate_new_key(self) -> str:
        """Generate new API key"""
        return f"tempo_{secrets.token_urlsafe(32)}"
```

### Firewall Configuration

**UFW Firewall Rules:**
```bash
# Reset firewall
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH access (adjust port as needed)
ufw allow 22/tcp

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Redis (internal only)
ufw allow from 172.18.0.0/16 to any port 6379

# Enable firewall
ufw enable
```

## Monitoring and Logging

### Application Monitoring

**Health Check Endpoint:**
```python
# routes/health.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import redis
import subprocess

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check for production monitoring"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "checks": {}
    }
    
    # Check Redis connectivity
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "response_time_ms": 0}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check disk space
    disk_usage = psutil.disk_usage('/')
    free_gb = disk_usage.free / (1024**3)
    if free_gb < 10:  # Less than 10GB free
        health_status["checks"]["disk"] = {"status": "warning", "free_gb": free_gb}
        if free_gb < 5:
            health_status["status"] = "unhealthy"
    else:
        health_status["checks"]["disk"] = {"status": "healthy", "free_gb": free_gb}
    
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        health_status["checks"]["memory"] = {"status": "warning", "usage_percent": memory.percent}
    else:
        health_status["checks"]["memory"] = {"status": "healthy", "usage_percent": memory.percent}
    
    # Check Celery workers
    try:
        result = subprocess.run(
            ["celery", "-A", "celery_app", "inspect", "ping"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            health_status["checks"]["celery"] = {"status": "healthy"}
        else:
            health_status["checks"]["celery"] = {"status": "unhealthy", "error": "No workers responding"}
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status

@router.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    from services.performance_cache import get_performance_monitor
    
    monitor = get_performance_monitor()
    summary = monitor.get_performance_summary()
    
    metrics = [
        f"tempo_requests_total {summary.get('total_requests', 0)}",
        f"tempo_cache_hit_rate {summary.get('cache_hit_rate_percent', 0) / 100}",
        f"tempo_avg_response_time_seconds {summary.get('processing_times', {}).get('average_seconds', 0)}",
        f"tempo_error_rate {summary.get('error_rate_percent', 0) / 100}",
    ]
    
    return "\n".join(metrics)
```

### Structured Logging

**Production Logging Configuration:**
```python
# config/logging.py
import logging
import logging.config
import os
from pythonjsonlogger import jsonlogger

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "/app/logs/application.log",
            "maxBytes": 50000000,  # 50MB
            "backupCount": 10
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "/app/logs/errors.log",
            "maxBytes": 50000000,
            "backupCount": 5
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

def setup_logging():
    """Setup production logging configuration"""
    os.makedirs("/app/logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
```

### Observability Stack

**Prometheus Configuration (prometheus.yml):**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tempo-api'
    static_configs:
      - targets: ['tempo-api:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "Tempo Processing API",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tempo_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "tempo_avg_response_time_seconds",
            "legendFormat": "Avg Response Time"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "tempo_cache_hit_rate * 100",
            "legendFormat": "Cache Hit %"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "tempo_error_rate * 100",
            "legendFormat": "Error %"
          }
        ]
      }
    ]
  }
}
```

## Scaling and Performance

### Horizontal Scaling

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tempo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tempo-api
  template:
    metadata:
      labels:
        app: tempo-api
    spec:
      containers:
      - name: tempo-api
        image: your-registry/tempo-api:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: tempo-api-service
spec:
  selector:
    app: tempo-api
  ports:
    - protocol: TCP
      port: 8001
      targetPort: 8001
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tempo-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tempo-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Performance Optimization

**Production Performance Settings:**
```python
# config/performance.py
import os

class ProductionConfig:
    # Celery optimization
    CELERY_WORKER_CONCURRENCY = int(os.getenv('CELERY_WORKER_CONCURRENCY', 4))
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_TASK_ACKS_LATE = True
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
    
    # Cache optimization
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 3600))
    MAX_CACHE_SIZE_MB = int(os.getenv('MAX_CACHE_SIZE_MB', 1000))
    
    # Rate limiting
    RATE_LIMIT_STORAGE = os.getenv('RATE_LIMIT_STORAGE', 'redis://redis:6379/1')
    RATE_LIMIT_STRATEGY = os.getenv('RATE_LIMIT_STRATEGY', 'sliding_window')
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    METRICS_COLLECTION_INTERVAL = int(os.getenv('METRICS_COLLECTION_INTERVAL', 60))
    
    # Resource limits
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', 10))
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 100))
    PROCESSING_TIMEOUT_SECONDS = int(os.getenv('PROCESSING_TIMEOUT_SECONDS', 1800))
```

## Backup and Recovery

### Data Backup Strategy

**Backup Script (backup.sh):**
```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Redis data
echo "Backing up Redis data..."
redis-cli --rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Backup application logs
echo "Backing up logs..."
tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" /app/logs/

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
    /app/.env.production \
    /app/gunicorn.conf.py \
    /etc/nginx/nginx.conf

# Clean up old backups
find "$BACKUP_DIR" -name "*backup_*.rdb" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

### Disaster Recovery Plan

**Recovery Procedures:**

1. **Service Recovery:**
```bash
# Restore from backup
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Monitor health
curl -f http://localhost:8001/health
```

2. **Data Recovery:**
```bash
# Restore Redis data
redis-cli FLUSHDB
redis-cli --pipe < /backups/redis_backup_latest.rdb

# Restore configuration
tar -xzf /backups/config_backup_latest.tar.gz -C /
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, load tests)
- [ ] Security scan completed
- [ ] Performance benchmarks meet requirements
- [ ] SSL certificates installed and valid
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Backup systems tested
- [ ] Monitoring dashboards configured

### Deployment Steps

- [ ] Deploy to staging environment
- [ ] Run full test suite on staging
- [ ] Perform load testing on staging
- [ ] Backup current production state
- [ ] Deploy to production with blue-green strategy
- [ ] Verify health checks pass
- [ ] Run smoke tests
- [ ] Monitor metrics for 1 hour
- [ ] Update documentation

### Post-Deployment

- [ ] Verify all services healthy
- [ ] Check error rates and response times
- [ ] Validate rate limiting works correctly
- [ ] Test backup and recovery procedures
- [ ] Update runbooks and procedures
- [ ] Set up alerting thresholds
- [ ] Schedule performance review

## Maintenance and Updates

### Regular Maintenance Tasks

**Weekly:**
- Review error logs and performance metrics
- Check disk space and memory usage
- Validate backup integrity
- Update security patches

**Monthly:**
- Performance optimization review
- Rate limit adjustment based on usage
- Cache cleanup and optimization
- Security audit

**Quarterly:**
- Dependency updates
- Scaling assessment
- Disaster recovery drill
- Performance baseline review

### Update Procedures

**Rolling Updates:**
```bash
# Update with zero downtime
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d --no-deps tempo-api
docker-compose -f docker-compose.production.yml up -d --no-deps celery-worker

# Verify deployment
curl -f http://localhost:8001/health
```

This production deployment guide provides comprehensive coverage of all aspects needed to successfully deploy and maintain the Tempo Processing API in a production environment.