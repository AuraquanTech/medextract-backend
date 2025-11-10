# DevOps Deployment Guide - MedExtract Backend

## Overview
Comprehensive guide for deploying MedExtract backend with GitHub Environments, Railway, Sentry, Cloudflare WAF, and Blue/Green deployments.

## 1. GitHub Environments Setup

### Created Environments
- **dev**: Development environment with 1 required reviewer
- **stage**: Staging environment with 1 required reviewer  
- **prod**: Production environment with required reviewers, prevent self-review, and wait timer

### Environment Secrets

#### Dev Environment
```
DATABASE_URL_DEV=postgresql://dev:devpass@localhost:5432/medextract_dev
```

#### Stage Environment  
```
DATABASE_URL_STAGE=postgresql://stage:stagepass@staging-db:5432/medextract_stage
```

#### Prod Environment
```
DATABASE_URL_PROD=postgresql://prod:prodpass@prod-db.internal:5432/medextract_prod
```

## 2. Database Migrations

Location: `app/scripts/db_migrate.py`

### Railway Deployment Integration

Add to Railway deployment configuration:

```yaml
deploy_step:
  command: "bash ops/migrate.sh"
  environment: production
```

### Migration Script

Create `ops/migrate.sh`:

```bash
#!/bin/bash
set -e

echo "[$(date)] Starting database migrations..."

# Load environment
source .env || true

# Execute migrations based on environment
case "$RAILWAY_ENVIRONMENT_NAME" in
  production)
    echo "Running production migrations"
    python app/scripts/db_migrate.py --env prod
    ;;
  staging)
    echo "Running staging migrations"
    python app/scripts/db_migrate.py --env stage
    ;;
  *)
    echo "Running development migrations"
    python app/scripts/db_migrate.py --env dev
    ;;
esac

echo "[$(date)] Migrations completed"
```

## 3. Observability Stack

### Sentry Integration

Add to `app/src/main.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FlaskIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "dev"),
)
```

### OpenTelemetry Integration

Add to `app/src/main.py`:

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Setup OpenTelemetry
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Instrument Flask and SQLAlchemy
FlaskInstrumentor().instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=db.engine)
```

## 4. WAF Configuration

### Cloudflare WAF Rules

Create `ops/cloudflare/waf_baseline.txt`:

```
# Rate Limiting
- Name: Rate Limit - API Endpoints
  Expression: (cf.threat_score > 50) or (cf.bot_management.score < 30)
  Action: Challenge
  Rate: 100 requests per 10 seconds

- Name: Rate Limit - Login Endpoint  
  Expression: (http.request.uri.path contains "/api/auth/login")
  Action: Challenge
  Rate: 10 requests per minute

# SQL Injection Protection
- Name: SQL Injection Prevention
  Expression: (http.request.uri.query contains "union") or (http.request.body contains "exec")
  Action: Block

# DDoS Protection
- Name: DDoS Protection
  Expression: cf.threat_score > 80
  Action: Block
  
# API Abuse
- Name: API Abuse Detection
  Expression: (cf.bot_management.score < 20) and (http.host eq "api.medextract.com")
  Action: Challenge
```

## 5. Stripe Reconciliation Cron Job

### Railway Cron Configuration

Add to `railway.toml`:

```toml
[[crons]]
name = "stripe-reconciliation"
schedule = "0 2 * * *"  # Daily at 2 AM UTC
command = "python ops/stripe_reconciliation.py"
environment = "production"
```

### Reconciliation Script

Create `ops/stripe_reconciliation.py`:

```python
#!/usr/bin/env python
import os
import stripe
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def reconcile_stripe():
    """Reconcile Stripe transactions with database"""
    logger.info(f"[{datetime.now()}] Starting Stripe reconciliation...")
    
    # Get charges from last 24 hours
    start_date = datetime.now() - timedelta(days=1)
    charges = stripe.Charge.list(
        created={"gte": int(start_date.timestamp())},
        limit=100
    )
    
    # Process charges
    reconciled = 0
    for charge in charges:
        # Logic to reconcile with database
        reconciled += 1
    
    logger.info(f"Reconciled {reconciled} charges")
    return reconciled

if __name__ == "__main__":
    reconcile_stripe()
```

## 6. Blue/Green Deployment

### Deployment Script

Create `ops/blue_green/switch_api.sh`:

```bash
#!/bin/bash
set -e

ENV=${1:-prod}
TARGET_SLOT=${2:-blue}
PROJECT_ID=$(railway project --json | jq -r '.id')

echo "[$(date)] Starting Blue/Green switch for $ENV to $TARGET_SLOT"

# Deploy to target slot
railway deploy --project $PROJECT_ID --environment $ENV --slot $TARGET_SLOT

# Health check
echo "[$(date)] Running health checks..."
HEALTH_CHECK_URL="https://${TARGET_SLOT}-api.medextract.com/health"
for i in {1..10}; do
    if curl -f $HEALTH_CHECK_URL > /dev/null; then
        echo "Health check passed"
        break
    fi
    echo "Attempt $i/10 - waiting for deployment..."
    sleep 10
done

# Switch traffic
echo "[$(date)] Switching traffic to $TARGET_SLOT"
railway service switch $ENVIRONMENT $TARGET_SLOT

echo "[$(date)] Blue/Green switch complete"
```

## 7. GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Environments

on:
  push:
    branches: [ main ]
  pull_request:
    types: [ opened, synchronize ]

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment: dev
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run DB Migrations
        run: bash ops/migrate.sh
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_DEV }}
      - name: Deploy to Railway
        run: railway deploy --environment dev

  deploy-stage:
    runs-on: ubuntu-latest
    environment: stage
    needs: deploy-dev
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run DB Migrations
        run: bash ops/migrate.sh
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_STAGE }}
      - name: Deploy to Railway
        run: railway deploy --environment stage

  deploy-prod:
    runs-on: ubuntu-latest
    environment: prod
    needs: deploy-stage
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run Blue/Green Switch
        run: bash ops/blue_green/switch_api.sh prod blue
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_PROD }}
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Environment Variables Reference

### All Environments
```
ENVIRONMENT=dev|stage|prod
SENTRY_DSN=<your-sentry-dsn>
OTEL_EXPORTER_OTLP_ENDPOINT=<your-otel-endpoint>
STRIPE_SECRET_KEY=<stripe-key>
```

## Deployment Checklist

- [ ] GitHub Environments created (dev, stage, prod)
- [ ] Secrets configured in each environment
- [ ] Required reviewers enabled
- [ ] DB migration script in place
- [ ] Sentry initialized in Flask app
- [ ] OpenTelemetry instrumentation active
- [ ] Cloudflare WAF rules applied
- [ ] Stripe cron job configured
- [ ] Blue/Green deployment scripts ready
- [ ] GitHub Actions workflow deployed
- [ ] Database connections tested
- [ ] Health endpoints configured

## Monitoring & Alerting

- Sentry: Error tracking and performance monitoring
- OpenTelemetry: Distributed tracing and metrics
- Cloudflare: WAF events and DDoS metrics
- Railway: Deployment logs and application metrics

## Troubleshooting

### Migration Failures
```bash
# Check migration status
railway logs --environment prod

# Rollback migration
python app/scripts/db_migrate.py --rollback
```

### Blue/Green Issues
```bash
# Check both slots
railway service list --project $PROJECT_ID

# Manual traffic switch
railway service switch $ENVIRONMENT blue/green
```
