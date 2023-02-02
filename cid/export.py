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
from cid.utils import get_parameter, get_parameters
from cid.helpers import pretty_sql
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

def enable_multiline_in_yaml():
    #https://stackoverflow.com/a/33300001
    def str_presenter(dumper, data):
      if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
      return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter) # to use with safe_dump

def escape_id(id_):
    return re.sub('[^0-9a-zA-Z]+', '-', id_)

def choose_analysis(qs):
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

    logger.info("analysing datasets")
    resources = {}
    resources['dashboards'] = {}
    resources['datasets'] = {}

    dataset_references = []
    datasets = {}
    all_views = []
    all_databases = [] 
    for dataset_arn in analysis['DataSetArns']:
        dependancy_views = []
        dataset_id = dataset_arn.split('/')[-1]
        dataset = qs.describe_dataset(dataset_id)

        if not isinstance(dataset, Dataset):
            raise CidCritical(f'dataset {dataset_id} not found. '
                'We need all datasets to be preset for template generation')

        dataset_references.append({
            "DataSetPlaceholder": dataset.raw['Name'],
            "DataSetArn": dataset_arn
        })

        dataset_data = {
            "DataSetId": dataset.raw['DataSetId'],
            "Name": dataset.raw['Name'],
            "PhysicalTableMap": dataset.raw['PhysicalTableMap'],
            "LogicalTableMap": dataset.raw['LogicalTableMap'],
            "ImportMode": dataset.raw['ImportMode'],
        }

        for key, value in dataset_data['PhysicalTableMap'].items():
            if 'RelationalTable' not in value \
                or 'DataSourceArn' not in value['RelationalTable'] \
                or 'Schema' not in value['RelationalTable']:
                raise CidCritical(f'Dataset {key} does not seems to be Antena dataset. Only Athena datasets are supported.' )
            all_databases.append(value['RelationalTable']['Schema'])
            value['RelationalTable']['DataSourceArn'] = '${athena_datasource_arn}'
            value['RelationalTable']['Schema'] = '${athena_database_name}'
            athena_source = value['RelationalTable']['Name']
            dependancy_views.append(athena_source)
            all_views.append(athena_source)

        for key, value in dataset_data.get('LogicalTableMap', {}).items():
            if 'Source' in value and "DataSetArn" in value['Source']:
                #FIXME add value['Source']['DataSetArn'] to the list of dataset_arn s 
                raise CidCritical(f"DataSet {dataset.raw['Name']} contains unsupported join. Please replace join of {value.get('Alias')} from DataSet to DataSource")


        datasets[dataset_arn] = {
            'data': dataset_data,
            'dependsOn': {'views': dependancy_views},
        }

    all_databases = list(set(all_databases))
    if len(all_databases) > 1:
        raise CidCritical(f'CID only supports one database. Multiple used: {all_databases}')

    athena.DatabaseName = all_databases[0]

    all_views_data = athena.process_views(all_views)
    for name, data in all_views_data.items():
        if 'CREATE EXTERNAL TABLE' not in data['data']:
            data['data'] = pretty_sql(data['data'])

    resources['views'] = all_views_data

    template_id = get_parameter(
        'template-id',
        message='Enter template id',
        default=escape_id(analysis['Name'].lower())
    )

    template_version_description = get_parameter(
        'template-version-description',
        message='Enter version description',
        default='vX.X.X' # FIXME: get version from analysis / template
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

    time.sleep(5)

    reader_account_id = get_parameter(
        'reader-account',
        message='Enter account id to share the template with or *',
        default='*'
    )
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

    dashboard_id = get_parameter(
        'dashboard-id',
        message='dashboard id (will be used in url of dashboard)',
        default=escape_id(analysis['Name'].lower())
    )

    resources['dashboards'][analysis['Name'].upper()] = {
        'name': analysis['Name'],
        'templateId': template_id,
        'sourceAccountId': qs.account_id,
        'region': qs.session.region_name,
        'dashboardId': dashboard_id,
        'dependsOn':{
            'datasets': [arn.split('/')[-1] for arn, dataset in datasets.items()]
        }
    }

    for arn, dataset in datasets.items():
        dataset_id = arn.split('/')[-1]
        resources['datasets'][dataset_id] = dataset

    output = get_parameter(
        'output',
        message='Enter a filename (.yaml)',
        default=f"{analysis['Name'].replace(' ', '-')}-{template_version_description}.yaml"
    )

    enable_multiline_in_yaml()
    with open(output, "w") as output_file:
        output_file.write(yaml.safe_dump(resources, sort_keys=False))


if __name__ == "__main__": # for testing
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('cid').setLevel(logging.DEBUG)
    qs = QuickSight(boto3.session.Session(), boto3.client('sts').get_caller_identity())
    athena = Athena(boto3.session.Session(), boto3.client('sts').get_caller_identity())
    export_analysis(qs, athena)

