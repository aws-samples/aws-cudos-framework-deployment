#!/bin/bash
# shellcheck disable=SC2086,SC2181
# This script runs cfn-lint cfn_nag_scan and checkov for all templates in folder

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

folder=$(git rev-parse --show-toplevel)/cfn-templates/
success_count=0
failure_count=0

# CKV_AWS_109: "Ensure IAM policies does not allow permissions management without constraints"
# CKV_AWS_111: "Ensure IAM policies does not allow write access without constraints"
# CKV_AWS_115: "Ensure that AWS Lambda function is configured for function-level concurrent execution limit"
# CKV_AWS_116: "Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)"
# CKV_AWS_117: "Ensure that AWS Lambda function is configured inside a VPC"
# CKV_AWS_173: "Check encryption settings for Lambda environmental variable"
# CKV_AWS_195: "Ensure Glue component has a security configuration associated"
# CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
# CKV_AWS_21: "Ensure the S3 bucket has versioning enabled"
checkov_skip=CKV_AWS_109,CKV_AWS_111,CKV_AWS_115,CKV_AWS_116,CKV_AWS_117,CKV_AWS_173,CKV_AWS_195,CKV_AWS_18,CKV_AWS_21


export exclude_files=("module-inventory.yaml" "module-pricing.yaml") # For::Each breaks lint :'(

yaml_files=$(find "$folder" -type f \( -name "*.yaml" -o -name "*.yml" \) -exec ls -1t "{}" +;) # ordered by date

for file in $yaml_files; do
    echo "Linting $(basename $file)"
    fail=0

    # checkov
    output=$(eval checkov  --skip-download --skip-check $checkov_skip --quiet -f "$file")
    if [ $? -ne 0 ]; then
        echo "$output" | awk '{ print "\t" $0 }'
        echo -e "checkov      ${RED}KO${NC}"  | awk '{ print "\t" $0 }'
        fail=1
    else
        echo -e "checkov      ${GREEN}OK${NC}"  | awk '{ print "\t" $0 }'
    fi

    # cfn-lint
    output=$(eval cfn-lint -- "$file")
    if [ $? -ne 0 ]; then
        echo "$output" | awk '{ print "\t" $0 }'
        echo -e "cfn-lint     ${RED}KO${NC}"  | awk '{ print "\t" $0 }'
        fail=1
    else
        echo -e "cfn-lint     ${GREEN}OK${NC}"  | awk '{ print "\t" $0 }'
    fi

    # cfn_nag_scan
    output=$(eval cfn_nag_scan --input-path "$file")
    if [ $? -ne 0 ]; then
        echo "$output" | awk '{ print "\t" $0 }'
        echo -e "cfn_nag_scan ${RED}KO${NC}"  | awk '{ print "\t" $0 }'
        fail=1
    else
        echo -e "cfn_nag_scan ${GREEN}OK${NC}"  | awk '{ print "\t" $0 }'
    fi

    if [ $fail -ne 0 ]; then
        ((failure_count++))
    else
        ((success_count++))
    fi
done

echo "Successful lints: $success_count"
echo "Failed lints:     $failure_count"
if [ $failure_count -ne 0 ]; then
    exit 1
else
    exit 0
fi
