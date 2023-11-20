'''
Source Account                    Destination Account
┌─────────────────────────┐       ┌──────────────────┐
│  Analysis    Template   │       │  Master Template │
│  ┌─┬──┬─┐    ┌──────┐   │       │    ┌──────┐      │
│  │ │┼┼│ ├────►      ├───┼───────┼────►      │      │
│  └─┴──┴─┘    └──────┘   │       │    └──────┘      │
│                         │       │                  │
└─────────────────────────┘       └──────────────────┘
'''
import re
import time
import logging

import yaml
import boto3

from cid.helpers import Dataset, QuickSight, Athena
from cid.helpers import CUR
from cid.utils import get_parameter, get_parameters, cid_print
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

def enable_multiline_in_yaml():
    """ Enable multiline in yaml

    credits: https://stackoverflow.com/a/33300001
    """
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:  # check for multiline string
            data =  re.sub(r'\s+$', '', data, flags=re.M) # Multiline does not support traling spaces
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter) # to use with safe_dump

def escape_id(id_):
    """ Escape id """
    return re.sub('[^0-9a-zA-Z]+', '-', id_)

def choose_analysis(qs):
    """ Choose analysis """
    try:
        analyzes = []
        logger.info("Discovering analyses")
        paginator = qs.client.get_paginator('list_analyses')
        response_iterator = paginator.paginate(
            AwsAccountId=qs.account_id,
            PaginationConfig={'MaxItems': 100}
        )
        for page in response_iterator:
            analyzes.extend(page.get('AnalysisSummaryList'))
        if len(analyzes) == 100:
            logger.info('Too many analyses. Will show first 100')
    except qs.client.exceptions.AccessDeniedException:
        logger.info("AccessDeniedException while discovering analyses")
        return None

    analyzes = list(filter(lambda a: a['Status']=='CREATION_SUCCESSFUL', analyzes ))
    if not analyzes:
        raise CidCritical("No analyses was found, please save your dashboard as an analyse first")
    choices = {a['Name']:a for a in sorted(analyzes, key=lambda a: a['LastUpdatedTime'])[::-1]}
    choice = get_parameter(
        'analysis-name',
        message='Select Analysis you want to share.',
        choices=choices.keys(),
    )
    return choices[choice]['AnalysisId']


def export_analysis(qs, athena):
    """ Export analysis to yaml resource File
    """

    enable_multiline_in_yaml()
    # Choose Analysis to share
    analysis_id = get_parameters().get('analysis-id') or choose_analysis(qs)

    if not analysis_id:
        analysis_id = get_parameter(
            'analysis-id',
            message='Enter ID of analysis you want to share (open analysis in browser and copy id from url)',
        )
    if not analysis_id:
        raise CidCritical("Need a parameter --analysis-id or --analysis-name")

    analysis = qs.client.describe_analysis(
        AwsAccountId=qs.account_id,
        AnalysisId=analysis_id
    )['Analysis']

    logger.info("analyzing datasets")
    resources = {}
    resources['dashboards'] = {}
    resources['datasets'] = {}


    cur_helper = CUR(session=athena.session)
    resources_datasets = []

    dataset_references = []
    datasets = {}
    all_views = []
    all_databases = []
    for dataset_arn in analysis['DataSetArns']:
        dependency_views = []
        dataset_id = dataset_arn.split('/')[-1]
        dataset = qs.describe_dataset(dataset_id)

        if not isinstance(dataset, Dataset):
            raise CidCritical(f'dataset {dataset_id} not found. '
                'We need all datasets to be preset for template generation')

        dataset_name = dataset.raw['Name']

        dataset_references.append({
            "DataSetPlaceholder": dataset_name,
            "DataSetArn": dataset_arn
        })

        cid_print(f'    Found DataSet <BOLD>{dataset_name}<END>.')
        if dataset_name in athena._resources.get('datasets'):
            resources_datasets.append(dataset_name)
            if not get_parameters().get('export-known-datasets'):
                cid_print(f'    DataSet <BOLD>{dataset_name}<END> is in resources. Skipping.')
                continue

        dataset_data = {
            "DataSetId": dataset.raw['DataSetId'],
            "Name": dataset.raw['Name'],
            "PhysicalTableMap": dataset.raw['PhysicalTableMap'],
            "LogicalTableMap": dataset.raw['LogicalTableMap'],
            "ImportMode": dataset.raw['ImportMode'],
        }

        for key, value in dataset_data['PhysicalTableMap'].items():
            if 'RelationalTable' in value \
                and 'DataSourceArn' in value['RelationalTable'] \
                and 'Schema' in value['RelationalTable']:
                logger.debug(f"Dataset {dataset.raw['DataSetId']} looks like classic athena dataset")
                value['RelationalTable']['DataSourceArn'] = '${athena_datasource_arn}'
                all_databases.append(value['RelationalTable']['Schema'])
                value['RelationalTable']['Schema'] = '${athena_database_name}'
                athena_source = value['RelationalTable']['Name']
                views_name = athena_source.split('.')[-1]
                dependency_views.append(views_name)
                if views_name in athena._resources.get('views') and not get_parameters().get('export-known-datasets'):
                    cid_print(f'    Athena view <BOLD>{views_name}<END> is in resources. Skipping')
                else:
                    all_views.append(views_name)
            elif 'CustomSql' in value and 'DataSourceArn' in value['CustomSql']:
                logger.debug(f"Dataset {dataset.raw['DataSetId']} looks like CustomSql athena dataset")
                value['CustomSql']['DataSourceArn'] = '${athena_datasource_arn}'
                databases = [db_['Name'] for db_ in athena.list_databases()]
                for database in databases:
                    if f'{database}.' in value['CustomSql']['SqlQuery'] or f'"{database}".' in value['CustomSql']['SqlQuery']:
                        logger.debug(f"Replacing {database} in text")
                        value['CustomSql']['SqlQuery'] = value['CustomSql']['SqlQuery'].replace(database, '${athena_database_name}')
                logger.warning(f"Dataset {dataset.raw['DataSetId']} use SqlQuery. Discovery of tables and views for that is not supported yet. Please add them manually")
            else:
                raise CidCritical(f"Dataset {key} {dataset.raw['Name']} do not seems to be Athena dataset. Only Athena datasets are supported." )

        for key, value in dataset_data.get('LogicalTableMap', {}).items():
            if 'Source' in value and "DataSetArn" in value['Source']:
                #FIXME add value['Source']['DataSetArn'] to the list of dataset_arn
                raise CidCritical(f"DataSet {dataset.raw['Name']} contains unsupported join. Please replace join of {value.get('Alias')} from DataSet to DataSource")

        dep_cur = False
        for dep_view in dependency_views[:]:
            if cur_helper.table_is_cur(name=dep_view):
                dependency_views.remove(dep_view)
                dep_cur = True
        datasets[dataset_name] = {
            'data': dataset_data,
            'dependsOn': {'views': dependency_views},
            'schedules': ['default'], #FIXME: need to read a real schedule
        }
        if dep_cur:
            datasets[dataset_name]['dependsOn']['cur'] = True

    all_databases = list(set(all_databases))
    if len(all_databases) > 1:
        raise CidCritical(f'CID only supports one database. Multiple used: {all_databases}')

    if all_databases:
        athena.DatabaseName = all_databases[0]

    cid_print(f'Analyzing Athena Views: <BOLD>{repr(all_views)}<END>. Can take some time.')
    all_views_data = athena.process_views(all_views)

    # Post processing of views:
    # - Special treatment for CUR: replace cur table with a placeholder
    # - Detect S3 paths as variables
    resources['views'] = {}
    cur_tables = []
    for key, view_data in all_views_data.items():
        if all_databases and isinstance(view_data.get('data'), str):
            view_data['data'] = view_data['data'].replace(f'{all_databases[0]}.', '${athena_database_name}.')

        if isinstance(view_data.get('data'), str):
            view_data['data'] = view_data['data'].replace('CREATE VIEW ', 'CREATE OR REPLACE VIEW ')

        # Analyse dependencies: if the dependency is CUR there is a special flag
        deps = view_data.get('dependsOn', {})
        non_cur_dep_views = []
        for dep_view in deps.get('views', []):
            dep_view_name = dep_view.split('.')[-1]
            if dep_view_name in cur_tables or cur_helper.table_is_cur(name=dep_view_name):
                logger.debug(f'{dep_view_name} is cur')
                view_data['dependsOn']['cur'] = True
                # replace cur table name with a variable
                if isinstance(view_data.get('data'), str):
                    # cur tables treated separately as we don't manage CUR table here
                    view_data['data'] = view_data['data'].replace(f'{dep_view_name}', '${cur_table_name}')
                cur_tables.append(dep_view_name)
            else:
                logger.debug(f'{dep_view_name} is not cur')
                if dep_view_name not in all_views_data:
                    logger.debug(f'{dep_view_name} skipping as not in the views list')
                non_cur_dep_views.append(dep_view_name)
        if deps.get('views'):
             deps['views'] = non_cur_dep_views
             if not deps['views']:
                del deps['views']

    logger.debug(f'cur_tables = {cur_tables}')
    # Add Views to Resources
    for key, view_data in all_views_data.items():
        if key in cur_tables or cur_helper.table_is_cur(name=key):
            logger.debug(f'Skipping {key} views - it is a CUR')
            continue
        if isinstance(view_data.get('data'), str):
            locations = re.findall(r"LOCATION\W+?'(s3://.+?)'", view_data.get('data'))
            for location in locations:
                logger.info(f'Please replace manually location bucket with a parameter: s3://{location}')
                default = get_parameter(
                    f'{key}-s3path',
                    'Please provide default value. (You can use {account_id} variable if needed)',
                    default=re.sub(r'(\d{12})', '{account_id}', location),
                    template_variables={'account_id': '{account_id}'},
                )
                view_data['parameters'] = {
                    f's3path': {
                        'default': default,
                        'description': f"S3 Path for {key} table",
                    }
                }
                view_data['data'] = view_data['data'].replace(location, '${s3path}')

        resources['views'][key] = view_data

    logger.debug('Building dashboard resource')
    dashboard_id = get_parameter(
        'dashboard-id',
        message='dashboard id (will be used in dashboard URL. Use lowercase, hyphens(not underscores) and make it short but understandable for humans)',
        default=escape_id(analysis['Name'].lower().replace(' ', '-').replace('_', '-'))
    )
    new_dashboard_id = dashboard_id.lower().replace(' ', '-').replace('_', '-')
    if dashboard_id != new_dashboard_id:
        cid_print('Best practices enforced: {dashboard_id} -> {new_dashboard_id}')
        dashboard_id = new_dashboard_id

    dashboard_resource = {}
    dashboard_resource['dependsOn'] = {
        # Historically CID uses dataset names as dataset reference. IDs of manually created resources have uuid format.
        # We can potentially reconsider this and use IDs at some point
        'datasets': sorted(list(set([dataset_name for dataset_name in datasets] + resources_datasets))) 
    }
    dashboard_resource['name'] = analysis['Name']
    dashboard_resource['dashboardId'] = dashboard_id
    dashboard_resource['category'] = get_parameters().get('category', 'Custom')

    dashboard_export_method = None
    if get_parameters().get('template-id'):
        dashboard_export_method = 'template'
    else:
        dashboard_export_method = get_parameter(
            'dashboard-export-method',
            message='Please choose export method',
            choices={
                '[template]   Generate a QuickSight Template in the current account (Recommended)': 'template',
                '[definition] Save QuickSight Dashboard Definition in the file': 'definition',
            },
        )
    if dashboard_export_method == 'template':
        template_id = get_parameter(
            'template-id',
            message='Enter template id',
            default=escape_id(analysis['Name'].lower())
        )
        default_description_version = 'v0.0.1'
        try:
            old_template = qs.client.describe_template(
                AwsAccountId=qs.account_id,
                TemplateId=template_id,
            )['Template']
            default_description_version = old_template.get('Version', {}).get('Description')
        except qs.client.exceptions.ResourceNotFoundException:
            logger.debug('No previous template')
        template_version_description = get_parameter(
            'template-version-description',
            message='Enter version description',
            default=default_description_version, # FIXME: get version from analysis / template
        )

        logger.info('Updating template')
        params = {
            "AwsAccountId": qs.account_id,
            "TemplateId": template_id,
            "Name": template_id,
            "SourceEntity": {
                "SourceAnalysis": {
                    "Arn": analysis.get("Arn"),
                    "DataSetReferences": dataset_references
                }
            },
            "VersionDescription": template_version_description,
        }
        logger.debug(f'Template params = {params}')
        try:
            res = qs.client.update_template(**params)
            logger.info(f'Template {template_id} updated from Analysis {analysis.get("Arn")}')
        except qs.client.exceptions.ResourceNotFoundException:
            res = qs.client.create_template(**params)
            logger.info(f'Template {template_id} created from Analysis {analysis.get("Arn")}')

        if res['CreationStatus'] not in ['CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
            raise CidCritical(f'failed template operation {res}')

        template_arn = res['Arn']
        logger.info(f'Template arn = {template_arn}')


        reader_account_id = get_parameter(
            'reader-account',
            message='Enter account id to share the template with or *',
            default='*'
        )

        time.sleep(5) # Some times update_template_permissions does not work immediately.

        res = qs.update_template_permissions(
            TemplateId=template_id,
            GrantPermissions=[
                {
                    "Principal": f'arn:aws:iam::{reader_account_id}:root' if reader_account_id != '*' else '*',
                    'Actions': [
                        "quicksight:DescribeTemplate",
                    ]
                },
            ],
        )
        dashboard_resource['templateId'] = template_id
        dashboard_resource['sourceAccountId'] = qs.account_id
        dashboard_resource['region'] = qs.session.region_name

    elif dashboard_export_method == 'definition':
        definition = qs.client.describe_analysis_definition(
            AwsAccountId=qs.account_id,
            AnalysisId=analysis_id,
        )['Definition']

        for dataset in definition.get('DataSetIdentifierDeclarations', []):
            # Hide region and account number of the source account
            dataset["DataSetArn"] = 'arn:aws:quicksight:::dataset/' + dataset["DataSetArn"].split('/')[-1]
        dashboard_resource['data'] = yaml.safe_dump(definition)

    resources['dashboards'][analysis['Name'].upper()] = dashboard_resource

    for name, dataset in datasets.items():
        resources['datasets'][name] = dataset

    output = get_parameter(
        'output',
        message='Enter a filename (.yaml)',
        default=f"{analysis['Name'].replace(' ', '-')}.yaml"
    )

    with open(output, "w", encoding='utf-8') as output_file:
        output_file.write(yaml.safe_dump(resources, sort_keys=False))
    cid_print(f'Output: <BOLD>{output}<END>')


if __name__ == "__main__": # for testing
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('cid').setLevel(logging.DEBUG)
    qs = QuickSight(boto3.session.Session(), boto3.client('sts').get_caller_identity())
    athena = Athena(boto3.session.Session(), boto3.client('sts').get_caller_identity())
    export_analysis(qs, athena)
