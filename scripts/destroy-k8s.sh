#!/bin/bash
# Heretek Swarm - Kubernetes Destroy Script
# Removes all deployed components from Kubernetes cluster

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
FORCE="${FORCE:-false}"

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
}

check_cluster() {
    if [ -n "$CONTEXT" ]; then
        kubectl config use-context "$CONTEXT"
    fi
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
}

confirm_destruction() {
    if [ "$FORCE" = "true" ]; then
        return
    fi

    echo ""
    log_warn "This will destroy ALL Heretek Swarm resources in namespace: $NAMESPACE"
    log_warn "This action cannot be undone!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Destruction cancelled."
        exit 0
    fi
}

delete_ingress() {
    log_info "Deleting ingress..."
    kubectl delete -f "$K8S_DIR/ingress.yaml" --ignore-not-found=true
}

delete_scaling() {
    log_info "Deleting autoscaling..."
    kubectl delete -f "$K8S_DIR/hpa.yaml" --ignore-not-found=true
}

delete_applications() {
    log_info "Deleting applications..."
    kubectl delete -f "$K8S_DIR/autonomous-deployment.yaml" --ignore-not-found=true
    kubectl delete -f "$K8S_DIR/dashboard-deployment.yaml" --ignore-not-found=true
    kubectl delete -f "$K8S_DIR/api-deployment.yaml" --ignore-not-found=true
}

delete_infrastructure() {
    log_info "Deleting infrastructure..."
    kubectl delete -f "$K8S_DIR/qdrant-deployment.yaml" --ignore-not-found=true
    kubectl delete -f "$K8S_DIR/redis-deployment.yaml" --ignore-not-found=true
    kubectl delete -f "$K8S_DIR/postgres-deployment.yaml" --ignore-not-found=true
}

delete_configmaps() {
    log_info "Deleting configmaps..."
    kubectl delete configmap -n "$NAMESPACE" --all --ignore-not-found=true
}

delete_secrets() {
    log_info "Deleting secrets..."
    kubectl delete secret -n "$NAMESPACE" --all --ignore-not-found=true
}

delete_namespace() {
    log_info "Deleting namespace: $NAMESPACE"
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
}

wait_for_deletion() {
    log_info "Waiting for resources to be deleted..."
    kubectl wait --for=delete namespace/"$NAMESPACE" --timeout=300s || true
}

# Main destruction flow
main() {
    log_info "Starting Heretek Swarm Kubernetes destruction..."
    echo ""

    check_kubectl
    check_cluster
    confirm_destruction

    delete_ingress
    delete_scaling
    delete_applications
    delete_infrastructure
    delete_configmaps
    delete_secrets
    delete_namespace
    wait_for_deletion

    echo ""
    log_info "Destruction completed successfully!"
    log_info "All Heretek Swarm resources have been removed from the cluster."
}

# Run main function
main "$@"
