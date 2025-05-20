#!/bin/bash
# get_cost_forecast.sh
# 
# Script for AWS Cost Explorer Forecast data collection
# This integrates with the CUDOS framework and collects forecast data
# to be used in QuickSight visualizations

# Strict error handling as per requirements
set -euo pipefail

# Configuration
: "${AWS_DEFAULT_REGION:=us-east-1}"
: "${FORECAST_BUCKET:=cid-data-$(aws sts get-caller-identity --query 'Account' --output text)}"
: "${FORECAST_PREFIX:=cost-explorer-forecast}"
: "${LOG_FILE:=/tmp/cost-explorer-forecast.log}"
: "${METRIC:=UNBLENDED_COST}"
: "${CONFIDENCE_LEVEL:=80}"
: "${GRANULARITY:=MONTHLY}"
: "${FORECAST_MONTHS:=12}"
: "${SERVICE_GROUPING:=true}"
: "${TIMESTAMP:=$(date +%Y-%m-%d-%H-%M-%S)}"

# Logging setup
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date +'%Y-%m-%dT%H:%M:%S%z')
    echo "[$timestamp] [$level] $message" | tee -a "${LOG_FILE}"
}

# Error handling
error_handler() {
    local exit_code=$?
    local line_number=$1
    log "ERROR" "Error on line ${line_number}, exit code ${exit_code}"
    exit ${exit_code}
}

trap 'error_handler $LINENO' ERR

log "INFO" "Starting Cost Explorer forecast data collection"
log "INFO" "Using AWS region: ${AWS_DEFAULT_REGION}"
log "INFO" "Data will be stored in s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is not installed. Please install it first."
    exit 1
fi

# Ensure the S3 bucket exists
if ! aws s3api head-bucket --bucket "${FORECAST_BUCKET}" 2>/dev/null; then
    log "WARN" "Bucket ${FORECAST_BUCKET} does not exist, trying to create it..."
    if aws s3 mb "s3://${FORECAST_BUCKET}" --region "${AWS_DEFAULT_REGION}"; then
        log "INFO" "Successfully created bucket ${FORECAST_BUCKET}"
    else
        log "ERROR" "Failed to create bucket ${FORECAST_BUCKET}"
        exit 1
    fi
fi

# Calculate date ranges
START_DATE=$(date +%Y-%m-01)
END_DATE=$(date -d "${START_DATE} +${FORECAST_MONTHS} months" +%Y-%m-01)

# Helper function to collect and store forecast data
collect_forecast() {
    local group_by=$1
    local output_file=$2
    
    log "INFO" "Collecting forecast data with grouping: ${group_by}"
    
    local cmd=("aws" "ce" "get-cost-forecast" 
               "--time-period" "Start=${START_DATE},End=${END_DATE}" 
               "--granularity" "${GRANULARITY}" 
               "--metric" "${METRIC}" 
               "--prediction-interval-level" "${CONFIDENCE_LEVEL}")
    
    if [ -n "${group_by}" ]; then
        cmd+=("--group-by" "Type=${group_by}")
    fi
    
    if "${cmd[@]}" > "${output_file}"; then
        log "INFO" "Successfully collected forecast data"
        return 0
    else
        log "ERROR" "Failed to collect forecast data"
        return 1
    fi
}

# Create temp directory for the results
TEMP_DIR=$(mktemp -d)
OVERALL_FORECAST="${TEMP_DIR}/overall_forecast.json"
SERVICE_FORECAST="${TEMP_DIR}/service_forecast.json"

# Collect overall forecast data (no grouping)
log "INFO" "Collecting overall forecast data"
collect_forecast "" "${OVERALL_FORECAST}"

# Collect service-grouped forecast data if enabled
if [ "${SERVICE_GROUPING}" = "true" ]; then
    log "INFO" "Collecting service-grouped forecast data"
    collect_forecast "SERVICE" "${SERVICE_FORECAST}"
fi

# Upload the data to S3
log "INFO" "Uploading forecast data to S3"
aws s3 cp "${OVERALL_FORECAST}" "s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/overall/${TIMESTAMP}.json"

if [ "${SERVICE_GROUPING}" = "true" ]; then
    aws s3 cp "${SERVICE_FORECAST}" "s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/by-service/${TIMESTAMP}.json"
fi

# Create a latest pointer file
echo "{\"timestamp\": \"${TIMESTAMP}\", \"path\": \"s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/overall/${TIMESTAMP}.json\"}" | \
    aws s3 cp - "s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/latest.json"

# Create Athena-friendly partitioned data
log "INFO" "Creating Athena-friendly partitioned data"

YEAR_MONTH=$(date +%Y-%m)
PARTITION_PATH="s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/partitioned/year=${YEAR_MONTH:0:4}/month=${YEAR_MONTH:5:2}"

# Transform the data into a flattened structure for Athena
jq -r '.ForecastResultsByTime[] | {
    dimension: "ALL",
    value: "ALL",
    metric: "'"${METRIC}"'",
    startdate: .TimePeriod.Start,
    enddate: .TimePeriod.End,
    meanvalue: .MeanValue,
    lowerbound: .PredictionIntervalLowerBound,
    upperbound: .PredictionIntervalUpperBound
}' "${OVERALL_FORECAST}" > "${TEMP_DIR}/athena_overall.json"

aws s3 cp "${TEMP_DIR}/athena_overall.json" "${PARTITION_PATH}/overall.json"

if [ "${SERVICE_GROUPING}" = "true" ]; then
    jq -c '.ForecastResultsByTime[] | .Groups[] | {
        dimension: "SERVICE",
        value: .Key,
        metric: "'"${METRIC}"'",
        startdate: .TimePeriod.Start,
        enddate: .TimePeriod.End,
        meanvalue: .MeanValue,
        lowerbound: .PredictionIntervalLowerBound,
        upperbound: .PredictionIntervalUpperBound
    }' "${SERVICE_FORECAST}" > "${TEMP_DIR}/athena_service.json"
    
    aws s3 cp "${TEMP_DIR}/athena_service.json" "${PARTITION_PATH}/by-service.json"
fi

# Clean up temp files
rm -rf "${TEMP_DIR}"

log "INFO" "Cost Explorer forecast data collection completed successfully"
log "INFO" "Data stored at s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/"

cat <<EOF

==========================================
AWS Cost Explorer Forecast Complete
==========================================
Data is now available in S3 at:
s3://${FORECAST_BUCKET}/${FORECAST_PREFIX}/

To use with CUDOS framework, run:
cid-cmd deploy --dashboard-id cost-forecast-dashboard

For more information, see:
https://github.com/aws-samples/aws-cudos-framework-deployment/blob/main/docs/cost_forecast.md
==========================================

EOF
