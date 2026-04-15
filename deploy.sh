#!/bin/bash
# Heretek Swarm - One-Shot Deployment Script
# This script handles the complete deployment process with a single command
# Usage: ./deploy.sh

set -e

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
LOG_FILE="${SCRIPT_DIR}/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Logging Functions
# =============================================================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
    echo "[STEP] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# =============================================================================
# Prerequisite Checks
# =============================================================================
check_docker() {
    log_step "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    log_info "Docker is installed and running (version: ${DOCKER_VERSION})"
}

check_docker_compose() {
    log_step "Checking Docker Compose installation..."
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
        log_info "Docker Compose is installed (version: ${COMPOSE_VERSION})"
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version | cut -d' ' -f4 | tr -d ',')
        log_info "Docker Compose plugin is installed (version: ${COMPOSE_VERSION})"
    else
        log_error "Docker Compose is not installed. Please install Docker Compose."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

check_disk_space() {
    log_step "Checking available disk space..."
    AVAILABLE_SPACE=$(df -P "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    MIN_SPACE=10485760  # 10GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$MIN_SPACE" ]; then
        log_warn "Low disk space: $((AVAILABLE_SPACE / 1024))MB available, 10GB recommended"
    else
        log_info "Disk space OK: $((AVAILABLE_SPACE / 1024))MB available"
    fi
}

check_memory() {
    log_step "Checking available memory..."
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -m | awk 'NR==2 {print $2}')
        MIN_MEM=4096  # 4GB
        
        if [ "$TOTAL_MEM" -lt "$MIN_MEM" ]; then
            log_warn "Low memory: ${TOTAL_MEM}MB available, 4GB recommended"
        else
            log_info "Memory OK: ${TOTAL_MEM}MB available"
        fi
    fi
}

# =============================================================================
# Environment Setup
# =============================================================================
setup_environment() {
    log_step "Setting up environment variables..."
    
    if [ -f "$ENV_FILE" ]; then
        log_info "Environment file already exists: $ENV_FILE"
        # Non-interactive: skip overwrite if .env already exists
    else
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_info "Environment file created from template: $ENV_FILE"
            log_warn "IMPORTANT: Edit $ENV_FILE and set your API keys before running services!"
        else
            log_error "No .env or .env.example found!"
        fi
    fi
}

# =============================================================================
# Service Deployment
# =============================================================================
deploy_services() {
    log_step "Deploying Heretek Swarm services..."
    
    cd "$SCRIPT_DIR"
    
    # Use docker compose (plugin) or docker-compose (standalone)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Pull latest images
    log_info "Pulling latest container images..."
    $COMPOSE_CMD pull
    
    # Start services
    log_info "Starting services..."
    $COMPOSE_CMD up -d
    
    # Wait for services to be healthy
    log_step "Waiting for services to be healthy..."
    sleep 10
    
    # Check service status
    $COMPOSE_CMD ps
}

# =============================================================================
# Health Checks
# =============================================================================
check_services() {
    log_step "Checking service health..."
    
    cd "$SCRIPT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec heretek-postgres pg_isready -U heretek -d heretek_swarm &> /dev/null; then
            log_info "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warn "PostgreSQL health check timed out"
        fi
        sleep 2
    done
    
    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker exec heretek-redis redis-cli ping &> /dev/null; then
            log_info "Redis is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warn "Redis health check timed out"
        fi
        sleep 2
    done
    
    # Wait for Qdrant
    log_info "Waiting for Qdrant to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/ &> /dev/null; then
            log_info "Qdrant is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warn "Qdrant health check timed out"
        fi
        sleep 2
    done
    
    echo ""
    log_info "Service Health Summary:"
    echo "  - PostgreSQL:  localhost:5432"
    echo "  - Redis:       localhost:6379"
    echo "  - Qdrant:      localhost:6333"
    echo "  - API Server:  localhost:8000"
    echo "  - Frontend:    localhost:3000"
}

# =============================================================================
# Database Migration
# =============================================================================
run_migrations() {
    log_step "Running database migrations..."
    
    # Wait a bit for PostgreSQL to be fully ready
    sleep 5
    
    # Run migrations if the script exists
    if [ -f "${SCRIPT_DIR}/scripts/run_migrations.py" ]; then
        log_info "Running database migrations..."
        cd "$SCRIPT_DIR"
        python scripts/run_migrations.py || log_warn "Migration script failed - may need manual execution"
    else
        log_info "Migration script not found - migrations may run automatically on container start"
    fi
}

# =============================================================================
# Usage Information
# =============================================================================
show_usage() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Heretek Swarm Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Services are now running. Access them at:"
    echo "  - API Server:  http://localhost:8000"
    echo "  - Frontend:    http://localhost:3000"
    echo "  - PostgreSQL:  localhost:5432"
    echo "  - Redis:       localhost:6379"
    echo "  - Qdrant:      localhost:6333"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:       docker-compose logs -f"
    echo "  - Stop services:   docker-compose down"
    echo "  - Restart:         docker-compose restart"
    echo "  - Check status:    docker-compose ps"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env file with your API keys"
    echo "  2. Run: docker-compose restart api"
    echo "  3. Access the dashboard at http://localhost:3000"
    echo ""
    echo "Documentation: See README.md for more details"
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Heretek Swarm - One-Shot Deploy      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    # Initialize log file
    echo "Deployment started: $(date)" > "$LOG_FILE"
    
    # Run prerequisite checks
    check_docker
    check_docker_compose
    check_disk_space
    check_memory
    
    echo ""
    
    # Setup environment
    setup_environment
    
    echo ""
    
    # Deploy services
    deploy_services
    
    echo ""
    
    # Run migrations
    run_migrations
    
    echo ""
    
    # Health checks
    check_services
    
    echo ""
    
    # Show usage
    show_usage
    
    log_info "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    stop)
        log_info "Stopping all services..."
        cd "$SCRIPT_DIR"
        if command -v docker-compose &> /dev/null; then
            docker-compose down
        else
            docker compose down
        fi
        log_info "Services stopped"
        ;;
    restart)
        log_info "Restarting all services..."
        cd "$SCRIPT_DIR"
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
        else
            docker compose restart
        fi
        log_info "Services restarted"
        ;;
    status)
        cd "$SCRIPT_DIR"
        if command -v docker-compose &> /dev/null; then
            docker-compose ps
        else
            docker compose ps
        fi
        ;;
    logs)
        cd "$SCRIPT_DIR"
        if command -v docker-compose &> /dev/null; then
            docker-compose logs -f
        else
            docker compose logs -f
        fi
        ;;
    clean)
        log_warn "This will remove all containers, networks, and volumes!"
        read -p "Are you sure? (y/N): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            cd "$SCRIPT_DIR"
            if command -v docker-compose &> /dev/null; then
                docker-compose down -v
            else
                docker compose down -v
            fi
            log_info "Cleanup complete"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|status|logs|clean}"
        exit 1
        ;;
esac
