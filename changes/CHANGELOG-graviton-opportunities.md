# What's new in the Graviton Opportunities Dashboard

## Graviton Opportunities Dashboard v1.1.1:
```
cid-cmd update --dashboard-id graviton-opportunities
Choose 'Yes' for the following prompt
[confirm-update] No updates available, should I update it anyway? 
```
* Fix broken hyperlinks under Additional Resources

## Graviton Opportunities Dashboard v1.1.0:
**Important:** If attempting to update the dashboard, please update cid-cmd first. To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id graviton-opportunities --force --recursive
```
**Bug fixes and improvements**
* Mordernization mapping updated with missing instance types
* Deleted Target Coverage and Efficiency sliders
* Including Savings Plan covered usage for EC2
* Updated Missing filters for RDS
* Updates to visuals
* New visuals for existing, potential coverage and implementation effort

## Graviton Opportunities Dashboard v1.0.3:
* Updated modernization mapping to include r8g
* Moved EC2 usage type filters from dashboard into SQL

## Graviton Opportunities Dashboard v1.0.2:
**Important:** If attempting to update the dashboard, please update cid-cmd first. To update run these commands in your CloudShell (recommended) or other terminal:

```
python3 -m ensurepip --upgrade
pip3 install --upgrade cid-cmd
cid-cmd update --dashboard-id graviton-opportunities --force --recursive
```

**Bug fixes and improvements**
 * Updates to visuals
 * Bug fix for duplicate resources caused by data collector storing multiple versions of upgraded resources


## Graviton Opportunities Dashboard v1.0.0
* Initial release
