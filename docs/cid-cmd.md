# CID-CMD - Cloud Intellegence Dashboards - CoMmanD line tool
CID-CMD is tool for managing QuickSight Dasboards. Also it manage Dashboard's dependancies, like Datasets, DataSources and Athena Views.

Syntax:
```bash
cid-cmd [tool parameters] [command] [command parameters]
```



## Commands

### deploy

### update

### delete

### map

### share

### export


## Tool Parameters
#### verbose
Generate a verbose log.
ex:
```bash
cid-cmd -vv deploy
```
See `cid.log` in the current folder

#### yes
Allways answer yes to yes/no questions

## Command Parameters

#### dashboard-id
QuickSight Dashboard ID (cudos, cost_intelligence_dashboard, kpi_dashboard, ta-organizational-view, trends-dashboard etc)

#### athena-database
Athena database

#### athena-workgroup
Athena workgroup

#### glue-data-catalog
Glue data catalog. Default = AwsDataCatalog

#### cur-table-name
CUR table name. A Name of Athena Table that contains all typucal fields of Cost & Usage Report.

#### quicksight-datasource-id
QuickSight DataSource ID

CID-CMD tool needs datasource arn for provisionning and update of DataSets. Only GLUE/Athena DataSources can be used and only in healthy state (CREATION_SUCCESSFUL|UPDATE_*).


If datasource parameter is omitted:
 - for update operations CID-CMD will determine the dataset from existing dataset
 - if no datasource found, CID-CMD will try to create one.
 - if only one datasource exists CID-CMD will use it
 - if multiple datasources found, CID-CMD will ask to choose one explictly 


#### quicksight-user
QuickSight user. 

#### dataset-{dataset_name}-id
QuickSight dataset id for a specific dataset. Can be useful if the tool is not able to list datasets due to perimissions issue. 

#### view-{view_name}-{parameter}
a custom parameter for a view creation, can use variable: {account_id}

#### account-map-source
Vales: `csv`, `dummy`, `organization` (if autodiscovery impossible)  
 `csv` - from csv. Format is the same as in  
 `dummy`  - fill table with account ids instead of names  
 `organization` - one time read organizations api  

If you do not know what to choose, choose `dummy`, and modify `account_map` later.

#### account-map-file
csv file path relative to current directory (if autodiscovery impossible and `csv` selected as a source )

#### resources
CID resources file (yaml)

#### share-with-account
Share dashboard with all users in the current account.
values:  ['yes/no']

