#!/bin/bash
set -euo pipefail

# Production deployment script for Abraxas v2.0.0

NAMESPACE="abraxas-prod"
RELEASE="abraxas"
CHART="./deployment/helm-chart/abraxas"
VALUES="./deployment/helm-chart/abraxas/values-prod.yaml"

echo "Deploying Abraxas v2.0.0 to production..."

# Create namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm (this will create the ConfigMap)
helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --values "$VALUES" \
  --wait --timeout 5m

# Verify deployment
echo "Verifying deployment..."
kubectl rollout status deployment/"$RELEASE" -n "$NAMESPACE" --timeout=300s

# Check health
POD=$(kubectl get pods -n "$NAMESPACE" -l app="$RELEASE" -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n "$NAMESPACE" "$POD" -- python scripts/health_check.py --check-all

echo "Deployment complete!"
echo "Access: http://localhost:8082 (via port-forward) or via Ingress if configured"