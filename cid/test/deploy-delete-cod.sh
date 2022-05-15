
cid-cmd -vv deploy  \
   --dashboard-id compute-optimizer-dashboard \
   --athena-database optimization_data \
   --view-compute-optimizer-lambda-lines-s3FolderPath       's3://costoptimizationdata{account_id}/Compute_Optimizer/Compute_Optimizer_lambda' \
   --view-compute-optimizer-ebs-volume-lines-s3FolderPath   's3://costoptimizationdata{account_id}/Compute_Optimizer/Compute_Optimizer_ebs_volume' \
   --view-compute-optimizer-auto-scale-lines-s3FolderPath   's3://costoptimizationdata{account_id}/Compute_Optimizer/Compute_Optimizer_auto_scale' \
   --view-compute-optimizer-ec2-instance-lines-s3FolderPath 's3://costoptimizationdata{account_id}/Compute_Optimizer/Compute_Optimizer_ec2_instance'



cid-cmd -vv -y delete \
   --dashboard-id compute-optimizer-dashboard \
   --athena-database optimization_data 


