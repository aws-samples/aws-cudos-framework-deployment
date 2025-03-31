## QuickSight Analysis Export and Import

1. Run `start-asset-bundle-export-job` to generate the CloudFormation template for deploying the QuickSight assets

    ```
    aws quicksight start-asset-bundle-export-job \
    --aws-account-id account-id \
    --asset-bundle-export-job-id cid-analysis \
    --resource-arn arn:aws:quicksight:us-east-1:account-id:analysis/analysis-id \
    --include-all-dependencies \
    --export-format CLOUDFORMATION_JSON \
    --include-permissions
    ```

1. Run to check export status
    ```
    aws quicksight describe-asset-bundle-export-job \
    --aws-account-id account-id \
    --asset-bundle-export-job-id cid-analysis
    ```

1. Once the status shows job completed successfully, download the CloudFormation template using the signed URL
    ```
    {
        "Status": 200,
        "JobStatus": "FAILED",
        "Errors": [
            {
                "Arn": "arn:aws:quicksight:us-east-1:account-id:analysis/CostIntelligenceDashboard",
                "Type": "com.amazonaws.services.quicksight.model.ResourceNotFoundException",
                "Message": "Analysis arn:aws:quicksight:us-east-1:account-id:analysis/CostIntelligenceDashboard is not found"
            }
        ],
        "Arn": "arn:aws:quicksight:us-east-1:account-id:asset-bundle-export-job/cid-analysis",
        "CreatedTime": "2025-03-30T11:59:51-04:00",
        "AssetBundleExportJobId": "cid-analysis",
        "AwsAccountId": "account-id",
        "ResourceArns": [
            "arn:aws:quicksight:us-east-1:account-id:analysis/CostIntelligenceDashboard"
        ],
        "IncludeAllDependencies": true,
        "ExportFormat": "CLOUDFORMATION_JSON",
        "RequestId": "request-id",
        "IncludePermissions": true,
        "IncludeTags": false,
        "IncludeFolderMemberships": false,
        "IncludeFolderMembers": "NONE"
    }

    {
        "Status": 200,
        "JobStatus": "IN_PROGRESS",
        "Arn": "arn:aws:quicksight:us-east-1:account-id:asset-bundle-export-job/cid-analysis",
        "CreatedTime": "2025-03-30T12:07:04-04:00",
        "AssetBundleExportJobId": "cid-analysis",
        "AwsAccountId": "account-id",
        "ResourceArns": [
            "arn:aws:quicksight:us-east-1:account-id:analysis/analysis-id"
        ],
        "IncludeAllDependencies": true,
        "ExportFormat": "CLOUDFORMATION_JSON",
        "RequestId": "request-id",
        "IncludePermissions": true,
        "IncludeTags": false,
        "IncludeFolderMemberships": false,
        "IncludeFolderMembers": "NONE"
    }

    {
        "Status": 200,
        "JobStatus": "SUCCESSFUL",
        "DownloadUrl": "https://quicksight-asset-bundle-export-job-us-east-1.s3.amazonaws.com/account-id/cid-analysis/some-id/assetbundle-cid-analysis.json?X-Amz-Security-Token=sometaken",
        "Arn": "arn:aws:quicksight:us-east-1:account-id:asset-bundle-export-job/cid-analysis",
        "CreatedTime": "2025-03-30T12:07:04-04:00",
        "AssetBundleExportJobId": "cid-analysis",
        "AwsAccountId": "account-id",
        "ResourceArns": [
            "arn:aws:quicksight:us-east-1:account-id:analysis/analysis-id"
        ],
        "IncludeAllDependencies": true,
        "ExportFormat": "CLOUDFORMATION_JSON",
        "RequestId": "request-id",
        "IncludePermissions": true,
        "IncludeTags": false,
        "IncludeFolderMemberships": false,
        "IncludeFolderMembers": "NONE"
    }

    ```
