# What's new in CUDOS Dashboard

## CUDOS Dashboard v4.26:
* Goals & Support moved to the Openning Sheet
* Controls: Filter by Account Name
* MoM Trends: Resource Level visuals performance tuning controls (for XXL accounts)
* Storage Summary: EBS Operations previous month; Action filters on visuals

# Upgrade path from 3.xx.x:

# “account_map” is now required by all SPICE datasets
* Add “account_map” with join clause “linked_account_id = account_id” to:
* s3_view
* ec2_running_cost
* compute_savings_plan_eligible_spend

# After you add “account_map”
Please do a git pull

```bash
git pull
./shell-script/lazymbr.sh update
  ```
