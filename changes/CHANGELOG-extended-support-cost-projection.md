# What's new in Extended Support Cost Projection

## Extended Support Cost Projection - v3.1.0

**Important:** This version requires the data collection version 3.2.0+. Update to this version requires a forced and recursive update. If you have modified the Extended Support Cost Projection dashboard view queries, they will be overridden when the dashboard is updated. Consider backing-up the existing view queries if they contain custom changes you want to keep so you can re-apply them after the update takes place.

To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id extended-support-cost-projection --force --recursive
```

## Extended Support Cost Projection - v3.0.0

**Important:** This version requires the data collection version 3.2.0+. Update to this version requires a forced and recursive update. If you have modified the Extended Support Cost Projection dashboard view queries, they will be overridden when the dashboard is updated. Consider backing-up the existing view queries if they contain custom changes you want to keep so you can re-apply them after the update takes place.

To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id extended-support-cost-projection --force --recursive
```

- Adjusted RDS queries to resolve Aurora Serverless databases for versions 1 and 2.

## Extended Support Cost Projection - v2.0.0

**Important:** Update to this version requires a forced and recursive update. If you have modified the Extended Support Cost Projection dashboard view queries, they will be overridden when the dashboard is updated. Consider backing-up the existing view queries if they contain custom changes you want to keep so you can re-apply them after the update takes place.

To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id extended-support-cost-projection --force --recursive
```

- Added Kubernetes version 1.30 to the calendar data in the EKS view definition.

## Extended Support Cost Projection - v1.2.0

**Important:** Update to this version requires a forced and recursive update. If you have modified the Extended Support Cost Projection dashboard view queries, they will be overridden when the dashboard is updated. Consider backing-up the existing view queries if they contain custom changes you want to keep so you can re-apply them after the update takes place.

To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id extended-support-cost-projection --force --recursive
```

You will be presented with the option "proceed and override" to update the RDS and EKS views. Please choose this option to ensure changes to the underlying view queries are applied in your RDS and EKS Extended support views.

- Adding preprocessing for RDS engine versions to simplify release calendar maintenance. Major versions will be used normally except in cases where minor versions are targeted for the extended support.
- Added remaining dates for the release calendar.
- Simplified release calendar maintenance by using only major version (or major.minor for where a minor version is targeted).
- Added account names and IDs to breakdown tables.
- Added start date for RDS Extended Support Estimated Cost Breakdown visual
- Increased size of EKS Extended Support Estimated Cost Breakdown to shows more items without scrolling
- Added action filters for all visuals in the dashboard

## v1.1.0
* Includes EKS Extended Support Cost Projection sheet.
* Adjusted titles for visuals showing estimated costs. Estimates are based on resource usage over a given period of time.
* Adjusted names for calculated fields and parameters.


## v1.0.0
* Initial release
* Includes RDS Extended Support Cost Projection and About sheets.
