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
import time
import logging

import yaml
import boto3

from cid.helpers import quicksight
from cid.utils import get_parameter, get_parameters
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

def export_analysis(qs):

    # Choose Analysis to share
    analysis_id = None
    if get_parameters().get('analysis-id'):
        analysis_id = get_parameters().get('analysis-id')

    if not analysis_id:
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
                logger.info('Too many analyzes. Will show first 100')
        except qs.client.exceptions.AccessDeniedException:
            logger.info("AccessDeniedException while discovering analyses")
        else:
            analyzes = list(filter(lambda a: a['Status']=='CREATION_SUCCESSFUL', analyzes ))
            choices = {a['Name']:a for a in sorted(analyzes, key=lambda a: a['LastUpdatedTime'])[::-1]}
            choice = get_parameter(
                'analysis-name',
                message='Select Analysis you want to share.',
                choices=choices.keys(),
            )
            analysis_id = choices[choice]['AnalysisId']

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
    dataset_references = []
    datasets = {}
    for dataset_arn in analysis['DataSetArns']:
        dataset_id = dataset_arn.split('/')[-1]
        dataset = qs.describe_dataset(dataset_id)

        if not isinstance(dataset, quicksight.Dataset):
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
            value['RelationalTable']['DataSourceArn'] = '${athena_datasource_arn}'
            value['RelationalTable']['Schema'] = '${athena_database_name}'

        datasets[dataset_arn] = dataset_data


    template_id = get_parameter(
        'template-id',
        message='Enter template id',
        default=analysis.get('Name').replace(' ', '-')
    )

    template_version_description = get_parameter(
        'template-version-description',
        message='Enter version description',
        default='vX.X.X' # FIXME: can we get the version from Analysis?
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
        "VersionDescription": template_version_description, # well actually version is not used, but i leave it as a reminder to update
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

    reader_account = get_parameter(
        'reader-account',
        message='Enter account id to share the template with or *',
        default='*'
    )
    res = qs.update_template_permissions(
        TemplateId=template_id,
        GrantPermissions=[
            {
                "Principal": {"AWS": reader_account} if reader_account != '*' else '*',
                'Actions': [
                    "quicksight:DescribeTemplate",
                ]
            },
        ],
    )

    resources = {}
    resources['dashboards'] = {}
    resources['datasets'] = {}
    resources['views'] = {}

    resources['dashboards'][analysis['Name'].upper()] = {
        'name': analysis['Name'],
        'templateId': template_id,
        'sourceAccountId': qs.account_id,
        'region': qs.session.region_name,
        'dashboardId': analysis['Name'].replace(' ', '-'),
        'dependsOn':{
            'datasets': [dataset['Name'].replace(' ', '-') for dataset in datasets.values()]
        }
    }

    for dataset in datasets.values():
        resources['datasets'][dataset.get("Name").replace(' ', '-')] = {'Data': dataset}

    output = get_parameter(
        'output',
        message='Enter a filename (.yaml)',
        default=f"{analysis['Name'].replace(' ', '-')}-{template_version_description}.yaml"
    )
    with open(output, "w") as output_file:
        output_file.write(yaml.safe_dump(resources, sort_keys=False))


if __name__ == "__main__": # for testing
    qs = quicksight.QuickSight(boto3.session.Session(), boto3.client('sts').get_caller_identity())
    export_analysis(qs)

