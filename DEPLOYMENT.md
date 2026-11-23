# Deployment Guide

## Overview

This guide provides detailed instructions for deploying the Release 1 Mobile Banking Platform across different environments, from local development through to production.

## Deployment Environments

| Environment | Purpose | Database | Deployment Method | Access |
|-------------|---------|----------|-------------------|--------|
| **Local** | Development and testing | SQLite | Manual (`start.sh`) | Localhost |
| **CI** | Automated testing | PostgreSQL (container) | GitHub Actions | N/A |
| **Staging** | Pre-production validation | Managed PostgreSQL | Automated (CD pipeline) | Private network |
| **Production** | Live customer environment | Managed PostgreSQL with PITR | Automated (CD pipeline) | Public (authenticated) |

## Prerequisites

### All Environments

- Git repository access
- Appropriate credentials and secrets
- Network connectivity to required services

### Local Development

- Python 3.11 or higher
- Node.js 20.19+ or 22+
- npm (comes with Node.js)
- Git (Git for Windows on Windows)

### Container Deployments

- Docker Engine 20.10+
- Docker Compose 2.0+
- Or Kubernetes 1.24+

### Managed Environments

- Access to container registry (GitHub Container Registry)
- Database provisioning permissions
- Cloud infrastructure access (AWS/Azure/GCP)

## Local Deployment

### Quick Start

**macOS / Linux / Windows (Git Bash):**
```bash
./start.sh
```

**Windows (Command Prompt):**
```cmd
start.bat
```

### Manual Setup

If you need to set up components individually:

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install .

# Copy environment file
cp dev.env .env

# Run migrations
alembic upgrade head

# Seed test data
python seed.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (requires backend running)
BACKEND_PORT=9000 npm run dev
```

### Stopping Local Services

```bash
./stop.sh  # macOS/Linux/Git Bash
# or
stop.bat   # Windows Command Prompt
```

## Docker Deployment

### SQLite Configuration (Default)

Best for: Local testing, demos, single-user scenarios

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f

# Access services
# Frontend: http://localhost:80
# Backend: http://localhost:9000
# API Docs: http://localhost:9000/docs

# Stop services
docker compose down

# Stop and remove data
docker compose down -v
```

### PostgreSQL Configuration

Best for: Multi-user testing, staging-like environment

```bash
# Build with PostgreSQL support
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build

# Start services
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.postgres.yml logs -f

# Access database
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec database psql -U lbgapp -d lbg_ftr_demo

# Stop services
docker compose -f docker-compose.yml -f docker-compose.postgres.yml down
```

### Docker Configuration Files

**Base Configuration (`docker-compose.yml`):**
- Backend service with SQLite
- Frontend service with nginx
- Named volume for SQLite data persistence

**PostgreSQL Override (`docker-compose.postgres.yml`):**
- PostgreSQL 15 service
- Backend configured for PostgreSQL
- PostgreSQL data volume

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Access to container registry
- Namespace created

### Deployment Steps

1. **Create namespace:**
   ```bash
   kubectl create namespace lbg-ftr-demo
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=database-url='postgresql+psycopg://user:pass@host:5432/db' \
     --from-literal=secret-key='your-secret-key-min-32-chars' \
     --namespace lbg-ftr-demo
   ```

3. **Apply Kubernetes manifests:**
   ```bash
   # Create from compose (using kompose)
   kompose convert -f docker-compose.yml
   kubectl apply -f . --namespace lbg-ftr-demo
   
   # Or use pre-created manifests if available
   kubectl apply -f k8s/ --namespace lbg-ftr-demo
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n lbg-ftr-demo
   kubectl get services -n lbg-ftr-demo
   ```

5. **Check logs:**
   ```bash
   kubectl logs -f deployment/backend -n lbg-ftr-demo
   kubectl logs -f deployment/frontend -n lbg-ftr-demo
   ```

6. **Access application:**
   ```bash
   # Port forward for testing
   kubectl port-forward service/frontend 8080:80 -n lbg-ftr-demo
   # Open http://localhost:8080
   ```

### Sample Kubernetes Manifests

**Backend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: lbg-ftr-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/<org>/lbg-ftr-demo-repo/backend:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: lbg-ftr-demo
spec:
  selector:
    app: backend
  ports:
  - port: 9000
    targetPort: 9000
  type: ClusterIP
```

**Frontend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: lbg-ftr-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: ghcr.io/<org>/lbg-ftr-demo-repo/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: BACKEND_HOST
          value: backend
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: lbg-ftr-demo
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

**Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: lbg-ftr-demo
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - lbg-ftr-demo.example.com
    secretName: app-tls
  rules:
  - host: lbg-ftr-demo.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

## Staging Deployment

### Overview

Staging is automatically deployed from the `main` branch via the CD pipeline.

### Configuration

**Database:**
- Managed PostgreSQL instance
- Automated backups enabled
- Point-in-time recovery enabled
- Connection pooling configured

**Environment Variables:**
```env
DATABASE_URL=postgresql+psycopg://user:pass@staging-db.example.com:5432/lbg_ftr_demo
SECRET_KEY=<staging-secret-key-32-chars-min>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_INACTIVITY_TIMEOUT_MINUTES=15
BCRYPT_COST_FACTOR=12
CORS_ORIGINS=https://staging.lbg-ftr-demo.example.com
RATE_LIMIT_ENABLED=true
PAYMENT_LIMIT_MINOR=100000000
FRESHNESS_TARGET_SECONDS=60
```

### Deployment Process

1. Code merged to `main` branch
2. CI pipeline runs and passes
3. CD pipeline builds container images
4. Images pushed to container registry
5. Database migrations applied
6. Backend containers updated
7. Frontend containers updated
8. Health checks executed
9. Smoke tests run
10. Deployment notification sent

### Verification

```bash
# Health check
curl https://staging.lbg-ftr-demo.example.com/health

# API health
curl https://staging.lbg-ftr-demo.example.com/api/health

# Frontend
curl -I https://staging.lbg-ftr-demo.example.com/
```

### Manual Staging Deployment

If needed to deploy manually:

```bash
# Trigger workflow manually
gh workflow run cd.yml -f environment=staging

# Or use kubectl
kubectl set image deployment/backend \
  backend=ghcr.io/<org>/lbg-ftr-demo-repo/backend:main-abc1234 \
  -n lbg-ftr-demo-staging

kubectl set image deployment/frontend \
  frontend=ghcr.io/<org>/lbg-ftr-demo-repo/frontend:main-abc1234 \
  -n lbg-ftr-demo-staging
```

## Production Deployment

### Overview

Production deployment is triggered by version tags and requires manual approval.

### Pre-Deployment Checklist

- [ ] All CI tests passing
- [ ] Staging deployment successful
- [ ] Staging smoke tests passing
- [ ] Database backup verified
- [ ] Rollback plan prepared
- [ ] Team notified of deployment window
- [ ] Monitoring dashboards ready

### Configuration

**Database:**
- Managed PostgreSQL with high availability
- Automated backups (hourly)
- Point-in-time recovery (7 days)
- Read replicas for scaling
- Connection pooling with PgBouncer

**Infrastructure:**
- Multi-zone deployment (2+ availability zones)
- Auto-scaling enabled (2-10 replicas)
- CDN for static assets
- DDoS protection enabled

**Environment Variables:**
```env
DATABASE_URL=postgresql+psycopg://user:pass@prod-db.example.com:5432/lbg_ftr_demo
SECRET_KEY=<production-secret-key-32-chars-min>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_INACTIVITY_TIMEOUT_MINUTES=15
BCRYPT_COST_FACTOR=12
CORS_ORIGINS=https://lbg-ftr-demo.example.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_PER_ADDRESS_MAX_ATTEMPTS=5
PAYMENT_LIMIT_MINOR=100000000
FRESHNESS_TARGET_SECONDS=60
```

### Deployment Process

1. Create version tag: `v1.2.3`
2. Push tag to GitHub
3. CI pipeline runs and passes
4. CD pipeline builds images
5. Images tagged with version
6. Manual approval requested
7. Database backup created
8. Database migrations applied (if any)
9. Blue/green deployment initiated
10. 10% traffic to new version
11. Health checks pass
12. 50% traffic to new version
13. Monitoring confirms stability
14. 100% traffic to new version
15. Old version kept for 1 hour
16. Smoke tests executed
17. Deployment complete

### Creating a Release

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create release tag
git tag -a v1.2.3 -m "Release v1.2.3: Payment improvements and security fixes"

# Push tag
git push origin v1.2.3

# Monitor deployment
gh run watch
```

### Monitoring Production

**Key Metrics:**
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Request rate
- Database connections
- Memory usage
- CPU usage

**Dashboards:**
- Application dashboard
- Database dashboard
- Infrastructure dashboard
- Business metrics dashboard

**Alerts:**
- Error rate > 1%
- Response time p95 > 2s
- Database connection exhaustion
- Memory usage > 80%
- Disk space < 20%

### Rollback Procedure

**Automated Rollback (if smoke tests fail):**
The CD pipeline automatically rolls back on failure.

**Manual Rollback:**

```bash
# Option 1: Revert to previous tag
gh workflow run cd.yml -f environment=production -f version=v1.2.2

# Option 2: Kubernetes rollback
kubectl rollout undo deployment/backend -n lbg-ftr-demo-prod
kubectl rollout undo deployment/frontend -n lbg-ftr-demo-prod

# Option 3: Blue/green switch
# Redirect traffic back to previous version
kubectl patch service frontend -p '{"spec":{"selector":{"version":"previous"}}}' -n lbg-ftr-demo-prod

# Verify rollback
kubectl rollout status deployment/backend -n lbg-ftr-demo-prod
kubectl rollout status deployment/frontend -n lbg-ftr-demo-prod
```

**Database Rollback:**

If migrations need to be rolled back:

```bash
# Connect to production database
kubectl exec -it deployment/backend -n lbg-ftr-demo-prod -- /bin/sh

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

## Database Management

### Backup Strategy

**Automated Backups:**
- Hourly snapshots (retained 24 hours)
- Daily snapshots (retained 30 days)
- Weekly snapshots (retained 90 days)
- Point-in-time recovery (7 days)

**Manual Backup:**
```bash
# Local SQLite
cp backend/app.db backend/app.db.backup

# PostgreSQL
pg_dump -U lbgapp -h localhost -d lbg_ftr_demo > backup.sql

# Kubernetes
kubectl exec deployment/database -n lbg-ftr-demo -- pg_dump -U lbgapp lbg_ftr_demo > backup.sql
```

### Migration Management

**Creating Migrations:**
```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "Add new column to payments"
```

**Applying Migrations:**
```bash
# Local
alembic upgrade head

# Docker
docker compose exec backend alembic upgrade head

# Kubernetes
kubectl exec deployment/backend -n lbg-ftr-demo -- alembic upgrade head
```

**Rolling Back Migrations:**
```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>

# Show current version
alembic current
```

### Database Maintenance

**Analyze and Vacuum (PostgreSQL):**
```bash
# Kubernetes
kubectl exec deployment/database -n lbg-ftr-demo -- psql -U lbgapp -d lbg_ftr_demo -c "ANALYZE;"
kubectl exec deployment/database -n lbg-ftr-demo -- psql -U lbgapp -d lbg_ftr_demo -c "VACUUM ANALYZE;"
```

**Check Database Size:**
```bash
kubectl exec deployment/database -n lbg-ftr-demo -- psql -U lbgapp -d lbg_ftr_demo -c "SELECT pg_size_pretty(pg_database_size('lbg_ftr_demo'));"
```

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker compose logs backend
kubectl logs deployment/backend -n lbg-ftr-demo

# Check events
kubectl describe pod <pod-name> -n lbg-ftr-demo

# Common causes:
# - Database connection failed
# - Missing environment variables
# - Migration not applied
# - Port already in use
```

**Database connection errors:**
```bash
# Test connection
docker compose exec backend python -c "from app.database import engine; print(engine.connect())"

# Check database is running
docker compose ps database
kubectl get pods -l app=database -n lbg-ftr-demo

# Check credentials
# Verify DATABASE_URL is correct
```

**Migrations fail:**
```bash
# Check current version
alembic current

# Check pending migrations
alembic heads

# Reset to specific version
alembic stamp <revision>

# Force migration
alembic upgrade head --sql > migration.sql
# Review migration.sql before applying
```

**High memory usage:**
```bash
# Check container resources
docker stats
kubectl top pods -n lbg-ftr-demo

# Check for memory leaks
# Review application logs for unusual patterns

# Increase memory limits if needed
# Update resource requests/limits in Kubernetes
```

## Security Considerations

### Secrets Management

**Never commit:**
- Database passwords
- API keys
- JWT secret keys
- Production environment files

**Use:**
- GitHub Secrets for CI/CD
- Kubernetes Secrets for clusters
- AWS Secrets Manager / Azure Key Vault for cloud
- Environment variables for local development

### Network Security

**Firewall Rules:**
- Backend accessible only from frontend
- Database accessible only from backend
- Management ports restricted to VPN

**TLS/SSL:**
- All external traffic over HTTPS
- Valid SSL certificates (Let's Encrypt or commercial)
- TLS 1.2 minimum

**Authentication:**
- Strong passwords enforced
- Rate limiting on auth endpoints
- Session timeout configured
- Token expiry enforced

## Performance Optimization

### Caching Strategy

**Application Level:**
- API response caching (60s for account data)
- Session caching (Redis in production)

**Database Level:**
- Connection pooling (10-50 connections)
- Query optimization
- Proper indexes on foreign keys

**CDN:**
- Static assets served via CDN
- Cache-Control headers configured
- Geographic distribution

### Scaling

**Horizontal Scaling:**
```bash
# Kubernetes
kubectl scale deployment/backend --replicas=5 -n lbg-ftr-demo
kubectl scale deployment/frontend --replicas=5 -n lbg-ftr-demo
```

**Auto-scaling:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Disaster Recovery

### Recovery Procedures

**Complete System Failure:**
1. Restore from latest database backup
2. Deploy last known good version
3. Verify data integrity
4. Run health checks
5. Gradually restore traffic

**Data Corruption:**
1. Identify corruption scope
2. Stop writes to affected tables
3. Restore from point-in-time backup
4. Verify data consistency
5. Resume operations

**Security Breach:**
1. Isolate affected systems
2. Rotate all credentials
3. Audit access logs
4. Patch vulnerabilities
5. Restore from clean backup if needed
6. Notify users if required

## Support and Contacts

**Technical Support:**
- Email: devops@example.com
- Slack: #lbg-ftr-demo-support
- On-call: PagerDuty rotation

**Documentation:**
- Repository: https://github.com/<org>/lbg-ftr-demo-repo
- Wiki: https://wiki.example.com/lbg-ftr-demo
- API Docs: https://lbg-ftr-demo.example.com/docs
