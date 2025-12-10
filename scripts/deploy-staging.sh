#!/bin/bash
# PEA RE Forecast Platform - Staging Deployment Script
# Usage: ./scripts/deploy-staging.sh
#
# Prerequisites:
# - kubectl configured with staging cluster access
# - helm 3.x installed
# - Docker images built and pushed to registry
#
# This script deploys the complete platform to staging.

set -e

NAMESPACE="pea-forecast"
HELM_RELEASE="pea-forecast"
HELM_CHART="infrastructure/helm/pea-re-forecast"
VALUES_FILE="infrastructure/helm/pea-re-forecast/values-staging.yaml"

echo "=========================================="
echo "PEA RE Forecast Platform - Staging Deploy"
echo "=========================================="
echo ""

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found. Please install kubectl."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "helm not found. Please install helm 3.x."; exit 1; }

# Verify cluster access
echo "1. Verifying cluster access..."
kubectl cluster-info || { echo "Cannot connect to cluster. Check your kubeconfig."; exit 1; }
echo "   Cluster connected."
echo ""

# Create namespace if not exists
echo "2. Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
echo "   Namespace ready."
echo ""

# Deploy observability stack
echo "3. Deploying observability stack..."
kubectl apply -f infrastructure/kubernetes/observability/namespace.yaml
kubectl apply -f infrastructure/kubernetes/observability/prometheus/
kubectl apply -f infrastructure/kubernetes/observability/grafana/
kubectl apply -f infrastructure/kubernetes/observability/alertmanager/
echo "   Observability stack deployed."
echo ""

# Deploy network policies
echo "4. Applying network policies..."
kubectl apply -f infrastructure/kubernetes/security/network-policies/
echo "   Network policies applied."
echo ""

# Deploy application via Helm
echo "5. Deploying application via Helm..."
if [ -f "${VALUES_FILE}" ]; then
    helm upgrade --install ${HELM_RELEASE} ${HELM_CHART} \
        --namespace ${NAMESPACE} \
        -f ${VALUES_FILE} \
        --wait --timeout 5m
else
    echo "   WARNING: ${VALUES_FILE} not found. Using default values."
    helm upgrade --install ${HELM_RELEASE} ${HELM_CHART} \
        --namespace ${NAMESPACE} \
        --wait --timeout 5m
fi
echo "   Application deployed."
echo ""

# Verify deployment
echo "6. Verifying deployment..."
kubectl get pods -n ${NAMESPACE}
echo ""

# Check services
echo "7. Services:"
kubectl get svc -n ${NAMESPACE}
echo ""

# Check ingress
echo "8. Ingress:"
kubectl get ingress -n ${NAMESPACE} 2>/dev/null || echo "   No ingress configured (may use port-forward)"
echo ""

echo "=========================================="
echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Verify pods are Running: kubectl get pods -n ${NAMESPACE}"
echo "  2. Check logs: kubectl logs -n ${NAMESPACE} -l app=backend"
echo "  3. Port-forward for testing: kubectl port-forward -n ${NAMESPACE} svc/backend 8000:8000"
echo "  4. Access API docs: http://localhost:8000/docs"
echo ""
echo "Observability:"
echo "  - Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "  - Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "=========================================="
