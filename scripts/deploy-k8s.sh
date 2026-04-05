#!/bin/bash
# Heretek Swarm - Kubernetes Deployment Script
# Deploys all components to Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="heretek-swarm"
K8S_DIR="./k8s"
CONTEXT="${KUBE_CONTEXT:-}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    log_info "kubectl is installed"
}

check_cluster() {
    if [ -n "$CONTEXT" ]; then
        kubectl config use-context "$CONTEXT"
    fi
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    log_info "Connected to Kubernetes cluster"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl apply -f "$K8S_DIR/namespace.yaml"
}

apply_secrets() {
    log_info "Applying secrets..."
    # Create secrets from environment variables
    envsubst < "$K8S_DIR/secrets.yaml" | kubectl apply -f -
}

apply_configmaps() {
    log_info "Applying configmaps..."
    kubectl apply -f "$K8S_DIR/configmaps.yaml"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure components..."
    kubectl apply -f "$K8S_DIR/postgres-deployment.yaml"
    kubectl apply -f "$K8S_DIR/redis-deployment.yaml"
    kubectl apply -f "$K8S_DIR/qdrant-deployment.yaml"
}

wait_for_infrastructure() {
    log_info "Waiting for infrastructure to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=qdrant -n "$NAMESPACE" --timeout=300s
    log_info "Infrastructure is ready"
}

deploy_applications() {
    log_info "Deploying applications..."
    kubectl apply -f "$K8S_DIR/api-deployment.yaml"
    kubectl apply -f "$K8S_DIR/dashboard-deployment.yaml"
    kubectl apply -f "$K8S_DIR/autonomous-deployment.yaml"
}

deploy_scaling() {
    log_info "Configuring autoscaling..."
    kubectl apply -f "$K8S_DIR/hpa.yaml"
}

deploy_ingress() {
    log_info "Deploying ingress..."
    kubectl apply -f "$K8S_DIR/ingress.yaml"
}

show_status() {
    log_info "Deployment status:"
    echo ""
    kubectl get all -n "$NAMESPACE"
    echo ""
    log_info "Ingress status:"
    kubectl get ingress -n "$NAMESPACE"
}

# Main deployment flow
main() {
    log_info "Starting Heretek Swarm Kubernetes deployment..."
    echo ""

    check_kubectl
    check_cluster
    create_namespace
    apply_secrets
    apply_configmaps
    deploy_infrastructure
    wait_for_infrastructure
    deploy_applications
    deploy_scaling
    deploy_ingress
    show_status

    echo ""
    log_info "Deployment completed successfully!"
    log_info "Access the dashboard at: http://dashboard.heretek-swarm.com"
    log_info "Access the API at: http://api.heretek-swarm.com"
}

# Run main function
main "$@"
