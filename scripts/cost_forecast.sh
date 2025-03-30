#!/bin/bash
# AWS Cost Forecast Data Fetch Tool
# Set strict error handling
set -euo pipefail

# Configuration
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly OUTPUT_DIR="${PWD}/output/${TIMESTAMP}"
readonly OUTPUT_FILE="${OUTPUT_DIR}/forecast_${TIMESTAMP}.csv"
readonly TEMP_DIR="${OUTPUT_DIR}/temp"
readonly MAX_PARALLEL=10  # Maximum parallel processes

# Create directories
mkdir -p "${OUTPUT_DIR}" "${TEMP_DIR}"

# Color codes and formatting
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[1;35m'
readonly NC='\033[0m'
readonly BOLD='\033[1m'
readonly UNDERLINE='\033[4m'
readonly BG_BLUE='\033[44m'
readonly BG_GREEN='\033[42m'

# Spinner characters
readonly SPINNER_CHARS='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

# Global variables for job tracking
declare -i total_jobs=0
declare -i completed_jobs=0
declare -i spinner_idx=0

# Available metrics
readonly METRICS=(
    "AMORTIZED_COST"
    "BLENDED_COST"
    "NET_AMORTIZED_COST"
    "NET_UNBLENDED_COST"
    "UNBLENDED_COST"
    "USAGE_QUANTITY"
    "NORMALIZED_USAGE_AMOUNT"
)

# Available dimensions
readonly DIMENSIONS=(
    "AZ"
    "INSTANCE_TYPE"
    "LINKED_ACCOUNT"
    "LINKED_ACCOUNT_NAME"
    "OPERATION"
    "PURCHASE_TYPE"
    "REGION"
    "SERVICE"
    "USAGE_TYPE"
    "USAGE_TYPE_GROUP"
    "RECORD_TYPE"
    "OPERATING_SYSTEM"
    "TENANCY"
    "SCOPE"
    "PLATFORM"
    "SUBSCRIPTION_ID"
    "LEGAL_ENTITY_NAME"
    "DEPLOYMENT_OPTION"
    "DATABASE_ENGINE"
    "INSTANCE_TYPE_FAMILY"
    "BILLING_ENTITY"
    "RESERVATION_ID"
    "SAVINGS_PLAN_ARN"
)

# Display functions
display_spinner() {
    local text="$1"
    printf "\r${CYAN}${SPINNER_CHARS:spinner_idx++:1}${NC} %s" "$text"
    spinner_idx=$(( spinner_idx >= ${#SPINNER_CHARS} ? 0 : spinner_idx ))
}

display_banner() {
    local text="$1"
    local width=60
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo
    echo -e "${BG_BLUE}${BOLD}$(printf '%*s' $width '')${NC}"
    echo -e "${BG_BLUE}${BOLD}$(printf '%*s' $padding '')${text}$(printf '%*s' $padding '')${NC}"
    echo -e "${BG_BLUE}${BOLD}$(printf '%*s' $width '')${NC}"
    echo
}

display_section_header() {
    local text="$1"
    echo -e "\n${YELLOW}${BOLD}═══════════════════ ${text} ═══════════════════${NC}\n"
}

display_progress_bar() {
    local progress=$1
    local text="${2:-Processing}"
    local width=40
    local filled=$(( progress * width / 100 ))
    local empty=$(( width - filled ))
    
    printf "\r${CYAN}${text}: ["
    printf "%${filled}s" '' | tr ' ' '█'
    printf "%${empty}s" '' | tr ' ' '░'
    printf "] %3d%%${NC}" $progress
}

# Rate limiting function
rate_limit() {
    sleep 0.5  # Half second delay between API calls
}

# Logging function
log() {
    local level=$1
    local message=$2
    local color
    
    case $level in
        "INFO") color="${CYAN}";;
        "SUCCESS") color="${GREEN}";;
        "WARNING") color="${YELLOW}";;
        "ERROR") color="${RED}";;
        *) color="${NC}";;
    esac
    
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') [${color}${level}${NC}] ${message}"
}

check_prerequisites() {
    display_section_header "CHECKING PREREQUISITES"
    local spinner_text="Checking AWS CLI..."
    
    display_spinner "${spinner_text}"
    if ! command -v aws >/dev/null 2>&1; then
        echo
        log "ERROR" "AWS CLI is not installed"
        exit 1
    fi
    
    spinner_text="Checking jq..."
    display_spinner "${spinner_text}"
    if ! command -v jq >/dev/null 2>&1; then
        echo
        log "ERROR" "jq is not installed"
        exit 1
    fi
    
    spinner_text="Checking AWS credentials..."
    display_spinner "${spinner_text}"
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        echo
        log "ERROR" "AWS credentials not configured"
        exit 1
    fi
    
    echo
    log "SUCCESS" "All prerequisites met"
}

get_time_period() {
    display_section_header "TIME PERIOD SELECTION"
    echo -e "${CYAN}${BOLD}Select Time Period:${NC}"
    echo -e "${MAGENTA}1)${NC} Next 30 days"
    echo -e "${MAGENTA}2)${NC} Next 90 days"
    echo -e "${MAGENTA}3)${NC} Next 180 days"
    echo -e "${MAGENTA}4)${NC} Next 365 days"
    echo -e "${MAGENTA}5)${NC} Custom period"
    
    echo -e "\n${BOLD}Enter your choice [1-5]:${NC}"
    read -p "→ " choice
    
    TODAY=$(date '+%Y-%m-%d')
    
    case $choice in
        1) END_DATE=$(date -d "${TODAY} +30 days" '+%Y-%m-%d');;
        2) END_DATE=$(date -d "${TODAY} +90 days" '+%Y-%m-%d');;
        3) END_DATE=$(date -d "${TODAY} +180 days" '+%Y-%m-%d');;
        4) END_DATE=$(date -d "${TODAY} +365 days" '+%Y-%m-%d');;
        5)
            echo -e "\n${BOLD}Enter end date (YYYY-MM-DD):${NC}"
            read -p "→ " END_DATE
            ;;
        *)
            log "ERROR" "Invalid choice"
            exit 1
            ;;
    esac
    
    START_DATE="${TODAY}"
    TIME_PERIOD="Start=${START_DATE},End=${END_DATE}"
    log "SUCCESS" "Time period set: ${START_DATE} to ${END_DATE}"
}

get_dimension_values() {
    local dimension=$1
    local values
    local spinner_text="Fetching values for ${dimension}..."
    
    display_spinner "${spinner_text}"
    rate_limit
    values=$(aws ce get-dimension-values \
        --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
        --dimension "${dimension}" \
        --query 'DimensionValues[*].Value' \
        --output json 2>/dev/null | jq -r '.[]' 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$values" ]]; then
        echo "$values"
    else
        echo
        log "WARNING" "No values found for dimension: ${dimension}"
        echo ""
    fi
}

fetch_forecast() {
    local dimension=$1
    local value=$2
    local metric=$3
    local output_file="${TEMP_DIR}/${dimension}_${value//\//_}_${metric}.json"
    
    local filter="{\"Dimensions\":{\"Key\":\"${dimension}\",\"Values\":[\"${value}\"]}}"
    
    rate_limit
    if aws ce get-cost-forecast \
        --time-period "${TIME_PERIOD}" \
        --metric "${metric}" \
        --granularity "${GRANULARITY}" \
        --prediction-interval-level 95 \
        --filter "${filter}" > "${output_file}" 2>/dev/null; then
        
        if [[ -f "${output_file}" ]]; then
            jq -r --arg dim "${dimension}" \
               --arg val "${value}" \
               --arg met "${metric}" \
               '.ForecastResultsByTime[] | [
                   $dim,
                   $val,
                   $met,
                   .TimePeriod.Start,
                   .TimePeriod.End,
                   .MeanValue,
                   .PredictionIntervalLowerBound,
                   .PredictionIntervalUpperBound
               ] | @csv' "${output_file}" >> "${OUTPUT_FILE}.tmp" 2>/dev/null
            
            rm "${output_file}"
        fi
    else
        log "WARNING" "Failed to fetch forecast for ${dimension}=${value}, metric=${metric}"
    fi
}

process_forecast_parallel() {
    echo "Dimension,Value,Metric,StartDate,EndDate,MeanValue,LowerBound,UpperBound" > "${OUTPUT_FILE}"
    touch "${OUTPUT_FILE}.tmp"

    # First, calculate total jobs and cache dimension values
    log "INFO" "Calculating total jobs..."
    declare -A dimension_values
    total_jobs=0
    
    for dimension in "${SELECTED_DIMENSIONS[@]}"; do
        log "INFO" "Fetching values for dimension: ${dimension}"
        # Cache dimension values in an array
        dimension_values[$dimension]=$(get_dimension_values "${dimension}")
        
        # Count number of values for this dimension
        value_count=$(echo "${dimension_values[$dimension]}" | wc -l)
        # Multiply by number of metrics
        dimension_total=$((value_count * ${#SELECTED_METRICS[@]}))
        total_jobs=$((total_jobs + dimension_total))
        
        log "INFO" "Found ${value_count} values for ${dimension}, adding ${dimension_total} jobs"
    done

    log "INFO" "Total jobs to process: ${total_jobs}"

    # Create a FIFO for job control
    mkfifo "${TEMP_DIR}/jobs.fifo"

    # Start background process to limit concurrent jobs
    exec 3<>"${TEMP_DIR}/jobs.fifo"
    for ((i=0; i<MAX_PARALLEL; i++)); do
        echo >&3
    done

    completed_jobs=0

    for dimension in "${SELECTED_DIMENSIONS[@]}"; do
        log "INFO" "Processing dimension: ${dimension}"
        
        echo "${dimension_values[$dimension]}" | while read -r value; do
            # Skip empty values
            [ -z "$value" ] && continue
            
            for metric in "${SELECTED_METRICS[@]}"; do
                # Wait for a slot
                read -u3
                {
                    fetch_forecast "${dimension}" "${value}" "${metric}"
                    echo >&3  # Release the slot
                    
                    # Update progress atomically
                    {
                        ((completed_jobs++))
                        progress=$((completed_jobs * 100 / total_jobs))
                        display_progress_bar $progress "Processing forecasts"
                    } 2>/dev/null
                } &
            done
        done
    done

    # Wait for all background jobs to complete
    wait

    # Clean up
    exec 3>&-
    rm "${TEMP_DIR}/jobs.fifo"

    # Combine results
    if [[ -f "${OUTPUT_FILE}.tmp" ]]; then
        cat "${OUTPUT_FILE}.tmp" >> "${OUTPUT_FILE}"
        rm "${OUTPUT_FILE}.tmp"
        echo  # New line after progress bar
        log "SUCCESS" "Data collection completed"
    else
        log "WARNING" "No data was collected"
    fi
}

select_options() {
    display_section_header "METRIC SELECTION"
    echo -e "${CYAN}${BOLD}Available Metrics:${NC}"
    echo -e "${MAGENTA}0)${NC} All metrics"
    
    for i in "${!METRICS[@]}"; do
        echo -e "${MAGENTA}$((i+1)))${NC} ${METRICS[$i]}"
    done
    
    echo -e "\n${BOLD}Enter your choice (0 for all, or comma-separated numbers):${NC}"
    read -p "→ " choices
    
    SELECTED_METRICS=()
    if [[ "$choices" == "0" ]]; then
        SELECTED_METRICS=("${METRICS[@]}")
        log "INFO" "Selected all metrics"
    else
        IFS=',' read -ra NUMS <<< "$choices"
        for num in "${NUMS[@]}"; do
            if [[ $num =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#METRICS[@]}" ]; then
                SELECTED_METRICS+=("${METRICS[$((num-1))]}")
            fi
        done
        log "INFO" "Selected ${#SELECTED_METRICS[@]} metrics"
    fi
    
    display_section_header "DIMENSION SELECTION"
    echo -e "${CYAN}${BOLD}Available Dimensions:${NC}"
    echo -e "${MAGENTA}0)${NC} All dimensions"
    
    for i in "${!DIMENSIONS[@]}"; do
        echo -e "${MAGENTA}$((i+1)))${NC} ${DIMENSIONS[$i]}"
    done
    
    echo -e "\n${BOLD}Enter your choice (0 for all, or comma-separated numbers):${NC}"
    read -p "→ " choices
    
    SELECTED_DIMENSIONS=()
    if [[ "$choices" == "0" ]]; then
        SELECTED_DIMENSIONS=("${DIMENSIONS[@]}")
        log "INFO" "Selected all dimensions"
    else
        IFS=',' read -ra NUMS <<< "$choices"
        for num in "${NUMS[@]}"; do
            if [[ $num =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#DIMENSIONS[@]}" ]; then
                SELECTED_DIMENSIONS+=("${DIMENSIONS[$((num-1))]}")
            fi
        done
        log "INFO" "Selected ${#SELECTED_DIMENSIONS[@]} dimensions"
    fi
    
    display_section_header "GRANULARITY SELECTION"
    echo -e "${CYAN}${BOLD}Select Granularity:${NC}"
    echo -e "${MAGENTA}1)${NC} DAILY"
    echo -e "${MAGENTA}2)${NC} MONTHLY"
    
    echo -e "\n${BOLD}Enter your choice [1-2]:${NC}"
    read -p "→ " choice
    
    case $choice in
        1) GRANULARITY="DAILY";;
        2) GRANULARITY="MONTHLY";;
        *) 
            log "ERROR" "Invalid choice"
            exit 1
            ;;
    esac
    log "INFO" "Selected ${GRANULARITY} granularity"
}

upload_to_s3() {
    echo -e "\n${BOLD}Enter S3 bucket name (or press Enter to skip):${NC}"
    read -p "→ " S3_BUCKET
    
    if [[ -n "${S3_BUCKET}" ]]; then
        local spinner_text="Uploading to S3..."
        display_spinner "${spinner_text}"
        if aws s3 cp "${OUTPUT_FILE}" "s3://${S3_BUCKET}/forecasts/$(basename ${OUTPUT_FILE})" >/dev/null 2>&1; then
            echo
            log "SUCCESS" "File uploaded to s3://${S3_BUCKET}/forecasts/$(basename ${OUTPUT_FILE})"
        else
            echo
            log "ERROR" "Failed to upload to S3"
            exit 1
        fi
    fi
}

generate_quicksight_manifest() {
    local csv_s3_uri="s3://${S3_BUCKET}/forecasts/$(basename ${OUTPUT_FILE})"
    local manifest_file="${OUTPUT_DIR}/manifest.json"
    
    log "INFO" "Generating QuickSight manifest file..."
    local spinner_text="Creating manifest..."
    display_spinner "${spinner_text}"
    
    cat > "${manifest_file}" << EOF
{
    "fileLocations": [
        {
            "URIs": [
                "${csv_s3_uri}"
            ]
        }
    ],
    "globalUploadSettings": {
        "format": "CSV",
        "delimiter": ",",
        "textqualifier": "\"",
        "containsHeader": "true"
    }
}
EOF

    if [[ -n "${S3_BUCKET}" ]]; then
        spinner_text="Uploading manifest to S3..."
        display_spinner "${spinner_text}"
        if aws s3 cp "${manifest_file}" "s3://${S3_BUCKET}/forecasts/manifest.json" >/dev/null 2>&1; then
            echo
            log "SUCCESS" "QuickSight manifest uploaded to s3://${S3_BUCKET}/forecasts/manifest.json"
            display_section_header "QUICKSIGHT SETUP"
            echo -e "${GREEN}${BOLD}QuickSight Import Instructions:${NC}"
            echo -e "${CYAN}1.${NC} In QuickSight, create a new dataset"
            echo -e "${CYAN}2.${NC} Choose 'S3' as the data source"
            echo -e "${CYAN}3.${NC} Use this manifest URL: s3://${S3_BUCKET}/forecasts/manifest.json"
            echo -e "${CYAN}4.${NC} Configure permissions to allow QuickSight to access the S3 bucket"
        else
            echo
            log "ERROR" "Failed to upload manifest file to S3"
        fi
    else
        echo
        log "INFO" "Manifest file created locally at: ${manifest_file}"
    fi
}

cleanup() {
    log "INFO" "Cleaning up temporary files..."
    rm -rf "${TEMP_DIR}"
}

main() {
    clear
    display_banner "AWS Cost Forecast Data Fetch Tool"
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    check_prerequisites
    get_time_period
    select_options
    
    display_section_header "PROCESSING"
    log "INFO" "Starting parallel forecast generation..."
    process_forecast_parallel
    
    if [[ -f "${OUTPUT_FILE}" ]]; then
        local records=$(wc -l < "${OUTPUT_FILE}")
        display_section_header "RESULTS"
        log "SUCCESS" "Generated forecast with $((records-1)) records"
        
        display_section_header "S3 UPLOAD"
        upload_to_s3
        
        if [[ -n "${S3_BUCKET}" ]]; then
            display_section_header "QUICKSIGHT CONFIGURATION"
            generate_quicksight_manifest
        fi
    else
        log "ERROR" "No forecast data generated"
        exit 1
    fi
}

main "$@"
