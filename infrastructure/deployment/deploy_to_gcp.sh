#!/usr/bin/env bash

# GCP Cloud Run Deployment Script for MCP Servers
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Project configured with billing enabled
#   - Cloud Run API enabled
#
# Usage:
#   ./deploy_to_gcp.sh                    # Deploy in development mode (unauthenticated)
#   ./deploy_to_gcp.sh --production       # Deploy in production mode (authenticated, VPC, secrets)
#   ./deploy_to_gcp.sh --server mcp-epic  # Deploy single server
#
# Modes:
#   Development: Public access, no VPC, no secrets, for testing
#                Deploys mcp-mockepic + mcp-mocktcga (synthetic data);
#                excludes mcp-epic (requires hospital FHIR secrets).
#   Production:  Authenticated, VPC, service accounts, secrets, HIPAA-compliant
#                (HOSPITAL1 profile): deploys mcp-epic (real FHIR R4);
#                excludes mcp-mockepic and mcp-mocktcga (external cBioPortal
#                MCP replaces mcp-mocktcga — deployed out-of-band).

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-precision-medicine-poc}"
REGION="${GCP_REGION:-us-central1}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Deployment mode (development or production)
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-development}"

# Production-specific configuration
VPC_CONNECTOR="${VPC_CONNECTOR:-mcp-connector}"  # Serverless VPC Connector name
VPC_EGRESS="${VPC_EGRESS:-all-traffic}"          # Route all traffic through VPC

# Parse command-line arguments
SINGLE_SERVER=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            DEPLOYMENT_MODE="production"
            shift
            ;;
        --development)
            DEPLOYMENT_MODE="development"
            shift
            ;;
        --server)
            SINGLE_SERVER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --production          Deploy in production mode (authenticated, VPC, secrets)"
            echo "  --development         Deploy in development mode (public access, default)"
            echo "  --server <name>       Deploy only specified server (e.g., mcp-epic)"
            echo "  --help                Show this help message"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Server configurations with resource requirements
# Format: "name:port:memory:cpu:env-vars:dry-run-flag"
#
# Profile notes:
#   - mcp-mockepic / mcp-mocktcga are development-only (synthetic data)
#   - mcp-epic is production-only (real Epic FHIR R4 sandbox / hospital)
#   The SERVERS array lists all candidates; apply_deployment_profile() below
#   filters them based on DEPLOYMENT_MODE before the deploy loop runs.
SERVERS=(
    "mcp-fgbio:3000:2Gi:2:FGBIO_LOG_LEVEL=INFO:FGBIO_DRY_RUN=false"
    "mcp-multiomics:3001:4Gi:2:MULTIOMICS_LOG_LEVEL=INFO:MULTIOMICS_DRY_RUN=false"
    "mcp-spatialtools:3002:4Gi:2:SPATIAL_LOG_LEVEL=INFO:SPATIAL_DRY_RUN=false"
    "mcp-mocktcga:3003:2Gi:2:MOCKTCGA_LOG_LEVEL=INFO:MOCKTCGA_DRY_RUN=true"
    "mcp-openimagedata:3004:2Gi:2:IMAGE_LOG_LEVEL=INFO:IMAGE_DRY_RUN=false"
    "mcp-deepcell:3007:2Gi:1:DEEPCELL_LOG_LEVEL=INFO:DEEPCELL_DRY_RUN=true"
    "mcp-mockepic:3008:2Gi:1:EPIC_LOG_LEVEL=INFO:DEIDENTIFY_ENABLED=true"
    "mcp-epic:3008:2Gi:1:EPIC_LOG_LEVEL=INFO:DEIDENTIFY_ENABLED=true"
    "mcp-perturbation:3009:4Gi:2:PERTURBATION_LOG_LEVEL=INFO:PERTURBATION_DRY_RUN=false"
    "mcp-quantum-celltype-fidelity:3010:2Gi:2:QUANTUM_BACKEND=cpu:QUANTUM_LOG_LEVEL=INFO"
    "mcp-patient-report:3011:2Gi:1:PATIENT_REPORT_LOG_LEVEL=INFO:PATIENT_REPORT_DRY_RUN=false"
    "mcp-genomic-results:3012:2Gi:1:GENOMIC_RESULTS_LOG_LEVEL=INFO:GENOMIC_RESULTS_DRY_RUN=false"
)

# Apply deployment profile to SERVERS array.
#
# - production (HOSPITAL1): exclude mcp-mockepic and mcp-mocktcga; keep mcp-epic.
#                           cBioPortal (replacement for mcp-mocktcga) is an
#                           external community MCP server and is not deployed
#                           by this script.
# - development:            exclude mcp-epic (requires Epic FHIR secrets that
#                           only exist in the hospital GCP project); keep the
#                           mock servers for CI and student Streamlit UIs.
#
# The filter is bypassed when --server <name> is used so operators can
# explicitly deploy a single server (e.g., testing mcp-epic against the
# Epic sandbox from a dev project) regardless of mode.
apply_deployment_profile() {
    if [ -n "$SINGLE_SERVER" ]; then
        return 0
    fi
    local filtered=()
    local entry
    local name
    for entry in "${SERVERS[@]}"; do
        name="${entry%%:*}"
        case "$DEPLOYMENT_MODE" in
            production)
                case "$name" in
                    mcp-mockepic|mcp-mocktcga) continue ;;
                esac
                ;;
            development)
                case "$name" in
                    mcp-epic) continue ;;
                esac
                ;;
        esac
        filtered+=("$entry")
    done
    SERVERS=("${filtered[@]}")
}
apply_deployment_profile

# Helper function to get server-specific secrets (production only)
get_server_secrets() {
    local server_name=$1
    case "$server_name" in
        mcp-epic)
            echo "EPIC_FHIR_ENDPOINT=epic-fhir-endpoint:latest,EPIC_CLIENT_ID=epic-client-id:latest,EPIC_CLIENT_SECRET=epic-client-secret:latest"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Helper function to get service account for server (production only)
get_service_account() {
    local server_name=$1
    case "$server_name" in
        mcp-fgbio) echo "mcp-fgbio-sa" ;;
        mcp-multiomics) echo "mcp-multiomics-sa" ;;
        mcp-spatialtools) echo "mcp-spatialtools-sa" ;;
        mcp-mocktcga) echo "mcp-mocktcga-sa" ;;
        mcp-openimagedata) echo "mcp-openimagedata-sa" ;;
        mcp-deepcell) echo "mcp-deepcell-sa" ;;
        mcp-epic) echo "mcp-epic-sa" ;;
        mcp-mockepic) echo "mcp-mockepic-sa" ;;
        mcp-perturbation) echo "mcp-perturbation-sa" ;;
        mcp-patient-report) echo "mcp-patient-report-sa" ;;
        mcp-quantum-celltype-fidelity) echo "mcp-quantum-sa" ;;
        mcp-genomic-results) echo "mcp-genomic-results-sa" ;;
        *) echo "" ;;
    esac
}

# Functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    print_success "gcloud CLI found"

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        print_error "Not authenticated. Run: gcloud auth login"
        exit 1
    fi
    print_success "Authenticated to GCP"

    # Set project
    gcloud config set project "${PROJECT_ID}" --quiet
    print_success "Project set to: ${PROJECT_ID}"

    # Enable required APIs
    print_info "Enabling required APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        artifactregistry.googleapis.com \
        --quiet
    print_success "APIs enabled"

    # Production mode: Additional prerequisite checks
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        print_info "Checking production prerequisites..."

        # Enable additional APIs for production
        gcloud services enable \
            vpcaccess.googleapis.com \
            secretmanager.googleapis.com \
            logging.googleapis.com \
            monitoring.googleapis.com \
            --quiet
        print_success "Production APIs enabled"

        # Check VPC connector exists
        if ! gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR}" \
                --region="${REGION}" \
                --project="${PROJECT_ID}" &> /dev/null; then
            print_error "VPC connector '${VPC_CONNECTOR}' not found"
            echo "Create VPC connector first:"
            echo "  cd infrastructure/hospital-deployment"
            echo "  ./setup-vpc.sh"
            exit 1
        fi
        print_success "VPC connector found: ${VPC_CONNECTOR}"

        # Check service accounts exist
        print_info "Verifying service accounts..."
        local missing_sa=0
        local sa_list="mcp-fgbio-sa mcp-multiomics-sa mcp-spatialtools-sa mcp-mocktcga-sa mcp-openimagedata-sa mcp-deepcell-sa mcp-epic-sa mcp-mockepic-sa mcp-perturbation-sa"
        for sa_name in $sa_list; do
            if ! gcloud iam service-accounts describe "${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
                    --project="${PROJECT_ID}" &> /dev/null; then
                print_error "Service account not found: ${sa_name}"
                ((missing_sa++))
            fi
        done

        if [ $missing_sa -gt 0 ]; then
            print_error "Missing ${missing_sa} service account(s)"
            echo "Create service accounts first:"
            echo "  cd infrastructure/hospital-deployment"
            echo "  ./setup-project.sh"
            exit 1
        fi
        print_success "All service accounts verified"

        # Check secrets exist (at least check for Epic secrets if deploying mcp-epic)
        if [ -z "$SINGLE_SERVER" ] || [ "$SINGLE_SERVER" = "mcp-epic" ]; then
            print_info "Verifying Epic FHIR secrets..."
            for secret in epic-fhir-endpoint epic-client-id epic-client-secret; do
                if ! gcloud secrets describe "$secret" --project="${PROJECT_ID}" &> /dev/null; then
                    print_error "Secret not found: $secret"
                    echo "Create secrets first:"
                    echo "  cd infrastructure/hospital-deployment"
                    echo "  ./setup-secrets.sh"
                    exit 1
                fi
            done
            print_success "Epic FHIR secrets verified"
        fi
    fi

    echo ""
}

# Deploy a single server
deploy_server() {
    local server_config=$1

    # Parse server configuration
    IFS=':' read -r server_name port memory cpu env_vars dry_run <<< "$server_config"

    local server_path="${REPO_ROOT}/servers/${server_name}"

    print_header "Deploying ${server_name} (${DEPLOYMENT_MODE} mode)"

    # Check if Dockerfile exists
    if [ ! -f "${server_path}/Dockerfile" ]; then
        print_error "Dockerfile not found at ${server_path}/Dockerfile"
        return 1
    fi

    print_info "Building and deploying from ${server_path}..."
    print_info "Resources: ${memory} memory, ${cpu} CPU"

    # Stage shared utilities for Docker build
    print_info "Staging shared utilities..."
    mkdir -p "${server_path}/_shared_temp"
    cp -r "${REPO_ROOT}/shared/utils" "${server_path}/_shared_temp/"

    # Build gcloud deploy command
    local deploy_cmd="gcloud run deploy ${server_name}"
    deploy_cmd+=" --source ${server_path}"
    deploy_cmd+=" --platform managed"
    deploy_cmd+=" --region ${REGION}"
    deploy_cmd+=" --memory ${memory}"
    deploy_cmd+=" --cpu ${cpu}"
    deploy_cmd+=" --min-instances 0"
    deploy_cmd+=" --max-instances 10"
    deploy_cmd+=" --timeout 300"

    # Base environment variables
    local all_env_vars="MCP_TRANSPORT=sse,ENVIRONMENT=${DEPLOYMENT_MODE},${env_vars},${dry_run}"

    # Production mode: Add authentication, VPC, service account, secrets
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        print_info "Production mode: Adding VPC, service account, and secrets..."

        # Require authentication (NO --allow-unauthenticated)
        deploy_cmd+=" --no-allow-unauthenticated"

        # VPC connector for hospital network integration
        deploy_cmd+=" --vpc-connector ${VPC_CONNECTOR}"
        deploy_cmd+=" --vpc-egress ${VPC_EGRESS}"

        # Ingress: Internal and Cloud Load Balancing (not public)
        deploy_cmd+=" --ingress internal-and-cloud-load-balancing"

        # Service account with least-privilege IAM
        local service_account="$(get_service_account "$server_name")"
        if [ -n "$service_account" ]; then
            deploy_cmd+=" --service-account ${service_account}@${PROJECT_ID}.iam.gserviceaccount.com"
            print_info "Using service account: ${service_account}"
        else
            print_error "No service account configured for ${server_name}"
            return 1
        fi

        # Server-specific secrets from Secret Manager
        local secrets="$(get_server_secrets "$server_name")"
        if [ -n "$secrets" ]; then
            deploy_cmd+=" --set-secrets ${secrets}"
            print_info "Loading secrets from Secret Manager"
        fi

        # Production environment variables
        deploy_cmd+=" --update-env-vars ${all_env_vars}"

        # Labels for production tracking
        deploy_cmd+=" --labels environment=production,hipaa-compliant=true,server=${server_name}"

    else
        # Development mode: Public access, no VPC, no secrets
        print_info "Development mode: Public access enabled"
        deploy_cmd+=" --allow-unauthenticated"
        deploy_cmd+=" --update-env-vars ${all_env_vars}"
        deploy_cmd+=" --labels environment=development,server=${server_name}"
    fi

    # Always quiet mode
    deploy_cmd+=" --quiet"

    # Execute deployment
    print_info "Executing: ${deploy_cmd}"
    eval "$deploy_cmd"

    if [ $? -eq 0 ]; then
        # Get the service URL
        SERVICE_URL=$(gcloud run services describe "${server_name}" \
            --platform managed \
            --region "${REGION}" \
            --format 'value(status.url)')

        print_success "Deployed: ${SERVICE_URL}"
        echo "${server_name}=${SERVICE_URL}" >> "${REPO_ROOT}/infrastructure/deployment_urls.txt"

        # Set MCP_BASE_URL for servers that serve file downloads
        if [ "${server_name}" = "mcp-patient-report" ]; then
            print_info "Setting MCP_BASE_URL=${SERVICE_URL} for download endpoint..."
            gcloud run services update "${server_name}" \
                --region "${REGION}" \
                --update-env-vars "MCP_BASE_URL=${SERVICE_URL}" \
                --quiet
        fi

        # Production mode: Display authentication info
        if [ "$DEPLOYMENT_MODE" = "production" ]; then
            print_info "⚠️  This service requires authentication"
            print_info "   Access via VPN: ${SERVICE_URL}"
        fi
    else
        print_error "Failed to deploy ${server_name}"
        # Cleanup staged files even on failure
        print_info "Cleaning up staged files..."
        rm -rf "${server_path}/_shared_temp"
        return 1
    fi

    # Cleanup staged files after successful deployment
    print_info "Cleaning up staged files..."
    rm -rf "${server_path}/_shared_temp"

    echo ""
}

# Test deployed server
test_server() {
    local server_name=$1
    local service_url=$2

    print_info "Testing ${server_name} at ${service_url}..."

    # Test health endpoint
    if curl -s -f "${service_url}/health" > /dev/null 2>&1; then
        print_success "${server_name} is healthy"
        return 0
    else
        print_error "${server_name} health check failed"
        return 1
    fi
}

# Main deployment function
main() {
    print_header "GCP Cloud Run Deployment - MCP Servers"
    echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
    echo -e "${BLUE}Region: ${REGION}${NC}"
    echo -e "${BLUE}Mode: ${DEPLOYMENT_MODE}${NC}"

    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        echo -e "${YELLOW}Production mode:${NC}"
        echo -e "${YELLOW}  - Authentication required${NC}"
        echo -e "${YELLOW}  - VPC connector: ${VPC_CONNECTOR}${NC}"
        echo -e "${YELLOW}  - Service accounts enabled${NC}"
        echo -e "${YELLOW}  - Secrets from Secret Manager${NC}"
        echo -e "${YELLOW}  - HIPAA-compliant configuration${NC}"
    else
        echo -e "${YELLOW}Development mode:${NC}"
        echo -e "${YELLOW}  - Public access (no authentication)${NC}"
        echo -e "${YELLOW}  - No VPC integration${NC}"
        echo -e "${YELLOW}  - Testing/development only${NC}"
    fi
    echo ""

    # Determine which servers to deploy
    local servers_to_deploy=()
    if [ -n "$SINGLE_SERVER" ]; then
        # Deploy single server
        for server_config in "${SERVERS[@]}"; do
            server_name="${server_config%%:*}"
            if [ "$server_name" = "$SINGLE_SERVER" ]; then
                servers_to_deploy+=("$server_config")
                break
            fi
        done

        if [ ${#servers_to_deploy[@]} -eq 0 ]; then
            print_error "Server not found: $SINGLE_SERVER"
            echo "Available servers:"
            for server_config in "${SERVERS[@]}"; do
                server_name="${server_config%%:*}"
                echo "  - $server_name"
            done
            exit 1
        fi

        print_info "Deploying single server: $SINGLE_SERVER"
    else
        # Deploy all servers
        servers_to_deploy=("${SERVERS[@]}")
        print_info "Deploying all ${#SERVERS[@]} servers"

        # Ask for confirmation
        read -p "Continue with deployment? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deployment cancelled"
            exit 0
        fi
    fi

    # Check prerequisites
    check_prerequisites

    # Clear previous deployment URLs (if deploying all)
    if [ -z "$SINGLE_SERVER" ]; then
        > "${REPO_ROOT}/infrastructure/deployment_urls.txt"
    fi

    # Deploy servers
    print_header "Starting Deployment"

    DEPLOYED=0
    FAILED=0

    for server_config in "${servers_to_deploy[@]}"; do
        if deploy_server "$server_config"; then
            ((DEPLOYED++))
        else
            ((FAILED++))
        fi
    done

    echo ""
    print_header "Deployment Summary"
    echo -e "${GREEN}Deployed: ${DEPLOYED}/${#servers_to_deploy[@]}${NC}"
    if [ $FAILED -gt 0 ]; then
        echo -e "${RED}Failed: ${FAILED}/${#servers_to_deploy[@]}${NC}"
    fi
    echo ""

    # Display all URLs
    if [ -f "${REPO_ROOT}/infrastructure/deployment_urls.txt" ]; then
        print_header "Deployed Server URLs"
        cat "${REPO_ROOT}/infrastructure/deployment_urls.txt"
        echo ""
    fi

    # Test deployed servers (skip in production mode - requires authentication)
    if [ "$DEPLOYMENT_MODE" = "development" ]; then
        print_header "Health Check Tests"
        while IFS='=' read -r server url; do
            test_server "$server" "$url" || true
        done < "${REPO_ROOT}/infrastructure/deployment_urls.txt"
    else
        print_info "Skipping health checks in production mode (authentication required)"
    fi

    echo ""
    print_header "Next Steps"

    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        echo -e "${YELLOW}Production Deployment:${NC}"
        echo -e "${YELLOW}1. Verify VPN access to deployed services${NC}"
        echo -e "${YELLOW}2. Test authentication with Azure AD SSO${NC}"
        echo -e "${YELLOW}3. Verify Epic FHIR connection (for mcp-epic)${NC}"
        echo -e "${YELLOW}4. Check audit logs in Cloud Logging${NC}"
        echo -e "${YELLOW}5. Review HIPAA compliance checklist${NC}"
        echo -e "${YELLOW}   See: /docs/hospital-deployment/HIPAA_COMPLIANCE.md${NC}"
    else
        echo -e "${YELLOW}Development Deployment:${NC}"
        echo -e "${YELLOW}1. Copy deployment_urls.txt URLs for Claude API config${NC}"
        echo -e "${YELLOW}2. Test servers: curl \${SERVICE_URL}/health${NC}"
        echo -e "${YELLOW}3. See docs/reference/testing/gcp-integration.md for integration${NC}"
        echo -e "${YELLOW}4. Deploy to production: ./deploy_to_gcp.sh --production${NC}"
    fi
    echo ""

    print_success "Deployment complete!"
}

# Run main function
main "$@"
