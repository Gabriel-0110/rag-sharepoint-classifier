#!/bin/bash
# SharePoint Automation Management Script
# Complete deployment and management for automatic SharePoint metadata classification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_DIR="/home/azureuser/rag_project"
CONDA_ENV="rag"
SERVICE_NAME="sharepoint-automation"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if conda environment exists
check_conda_env() {
    print_status "Checking conda environment..."
    if conda env list | grep -q "^${CONDA_ENV} "; then
        print_success "Conda environment '${CONDA_ENV}' exists"
        return 0
    else
        print_error "Conda environment '${CONDA_ENV}' not found"
        return 1
    fi
}

# Function to activate conda environment
activate_conda() {
    source /home/azureuser/miniconda3/etc/profile.d/conda.sh
    conda activate ${CONDA_ENV}
}

# Function to check required services
check_services() {
    print_status "Checking required services..."
    
    # Check Qdrant
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        print_success "Qdrant vector database: RUNNING"
    else
        print_warning "Qdrant vector database: NOT ACCESSIBLE"
        print_status "Starting Qdrant..."
        # Add Qdrant startup command if needed
    fi
    
    # Check Mistral API
    if pgrep -f "mistral_api_server" > /dev/null; then
        print_success "Mistral API server: RUNNING"
    else
        print_warning "Mistral API server: STOPPED"
        print_status "You may need to start Mistral API server manually"
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    activate_conda
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Function to test the automation
test_automation() {
    print_status "Testing SharePoint automation..."
    activate_conda
    cd ${PROJECT_DIR}
    
    # Test single run
    AUTOMATION_MODE=once python3 sharepoint_automation.py
    
    if [ $? -eq 0 ]; then
        print_success "Automation test completed successfully"
    else
        print_error "Automation test failed"
        return 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting SharePoint automation service..."
    
    sudo systemctl start ${SERVICE_NAME}
    sleep 3
    
    if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
        print_success "SharePoint automation service started"
    else
        print_error "Failed to start SharePoint automation service"
        sudo systemctl status ${SERVICE_NAME}
        return 1
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping SharePoint automation service..."
    sudo systemctl stop ${SERVICE_NAME}
    print_success "SharePoint automation service stopped"
}

# Function to show status
show_status() {
    print_status "System Status Dashboard"
    echo "=========================================="
    
    activate_conda
    cd ${PROJECT_DIR}
    python3 monitor_automation.py
}

# Function to show logs
show_logs() {
    print_status "Recent service logs:"
    sudo journalctl -u ${SERVICE_NAME} -f --no-pager
}

# Function to deploy everything
deploy_all() {
    print_status "🚀 Starting complete deployment..."
    
    cd ${PROJECT_DIR}
    
    # Check environment
    if ! check_conda_env; then
        print_error "Cannot proceed without conda environment"
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Check services
    check_services
    
    # Test automation
    if ! test_automation; then
        print_error "Automation test failed, deployment aborted"
        exit 1
    fi
    
    # Install systemd service
    print_status "Installing systemd service..."
    sudo cp sharepoint-automation.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    
    # Start services
    start_services
    
    print_success "🎉 Deployment completed successfully!"
    print_status "SharePoint automation is now running and will auto-start on boot"
    print_status "Use './manage_automation.sh status' to monitor the system"
}

# Function to show help
show_help() {
    echo "SharePoint Automation Management Script"
    echo "========================================"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      - Complete deployment and setup"
    echo "  start       - Start automation service"
    echo "  stop        - Stop automation service"
    echo "  restart     - Restart automation service"
    echo "  status      - Show system status and monitoring dashboard"
    echo "  logs        - Show real-time service logs"
    echo "  test        - Test automation in single-run mode"
    echo "  install     - Install dependencies only"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy           # Complete setup"
    echo "  $0 status           # Check system status"
    echo "  $0 logs             # Monitor logs"
}

# Main script logic
case "${1:-help}" in
    deploy)
        deploy_all
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_automation
        ;;
    install)
        install_dependencies
        ;;
    help|*)
        show_help
        ;;
esac
