# What's new in the Compute Optimizer Dashboard (COD)

## Compute Optimizer Dashboard - v2.0.2
* Added History Visual on EBS tab

## Compute Optimizer Dashboard - v2.0.1
* Bugfixes

## Compute Optimizer Dashboard - v2.0.0
* Added support of Tags. Currently dashboard use 2 tags (primary and secondary). You can specify on install or update. Values of these tags can be used in filters.
* Added finding history, showing all availabe findings for a particualr resource over time.
* Added AccountId and BU filters.

**Important:** Update to this version requires cid-cmd v0.2.18+.

```
pip3 install --upgrade cid-cmd
cid-cmd update --dashboards-id compute-optimizer-dashboard --force --recursive --on-drift override
```

## Compute Optimizer Dashboard - v1.0
* Initial release