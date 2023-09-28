""" Test of Dashboard creation with the right permission.

Test CID creation via CFN with the correct roles

Personas:
    - Admin: a person with full admin access
    - Finops who needs to deploy CID via CFN

Procedure:
    1. Admin creates a role and adds policies to the role
    2. Finops using this role creates CUR and deploys CID
    3. Verify dashboard exists
    3. Delete all in reverse order

This must be executed with admin priveleges.
"""
import os
import json
import time
import logging

import boto3

logger = logging.getLogger(__name__)

# Console Colors
HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
WARNING = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

account_id = boto3.client('sts').get_caller_identity()['Account']


def delete_bucket(name): # move to tools
    """delete all content and the bucket"""
    s3r = boto3.resource('s3')
    try:
        s3r.Bucket(name).object_versions.delete()
    except Exception: # nosec B110 pylint: disable=broad-exception-caught
        pass
    s3c = boto3.client('s3')
    try:
        s3c.delete_bucket(Bucket=name)
    except s3c.exceptions.NoSuchBucket:
        pass

def upload_to_s3(filename): # move to tools
    """upload file object to a temporary bucket and return a public url"""
    path = os.path.basename(filename)
    s3c = boto3.client('s3')
    bucket = f'{account_id}-cid-tests-deleteme'
    try:
        s3c.create_bucket(Bucket=bucket)
    except s3c.exceptions.BucketAlreadyExists:
        pass
    s3c.upload_file(filename, bucket, path)
    return f'https://{bucket}.s3.amazonaws.com/{path}'

def format_event(stack, event): # move to tools
    """format event line"""
    line = '\t'.join([
        event['Timestamp'].strftime("%H:%M:%S"),
        stack,
        event['LogicalResourceId'],
        event['ResourceStatus'],
        event.get('ResourceStatusReason',''),
    ])
    color = END
    if '_COMPLETE' in line:
        color = GREEN
    elif '_FAILED' in line or 'failed to create' in line:
        color = RED
    return f'{color}{line}{END}'


def watch_stacks(cloudformation, stacks=None): # move to tools
    """ watch stacks while they are IN_PROGRESS and/or until they are deleted"""
    stacks = stacks or []
    last_update = {stack: None for stack in stacks}
    in_progress = True
    while stacks and in_progress:
        time.sleep(5)
        in_progress = False
        for stack in stacks[:]:
            # Check events
            events = []
            try:
                events = cloudformation.describe_stack_events(StackName=stack)['StackEvents']
            except cloudformation.exceptions.ClientError as exc:
                if 'does not exist' in exc.response['Error']['Message']:
                    stacks.remove(stack)
                logger.info(exc.response['Error']['Message'])
            for event in events:
                if last_update.get(stack) and last_update.get(stack) >= event['Timestamp']:
                    continue
                logger.info(format_event(stack, event))
                last_update[stack] = event['Timestamp']
            try:
                # Check stack status
                current_stack = cloudformation.describe_stacks(StackName=stack)['Stacks'][0]
                if 'IN_PROGRESS' in current_stack['StackStatus']:
                    in_progress = True
                # Check nested stacks and add them to tracking
                for res in cloudformation.list_stack_resources(StackName=stack)['StackResourceSummaries']:
                    if res['ResourceType'] == 'AWS::CloudFormation::Stack':
                        name = res['PhysicalResourceId'].split('/')[-2]
                        if name not in stacks:
                            stacks.append(name)
            except: # nosec B110 using in tests; pylint: disable=bare-except
                pass

def get_qs_user(): # move to tools
    """ get any valid qs user """
    qs_ = boto3.client('quicksight')
    users = qs_.list_users(AwsAccountId=account_id, Namespace='default')['UserList']
    assert users, 'No QS users, pleas create one.' # nosec B101:assert_used
    return users[0]['UserName']

def timeit(method): # move to tools
    """timing decorator"""
    def timed(*args, **kwargs):
        start = time.time()
        result = method(*args, **kwargs)
        end = time.time()
        print(f'{method.__name__} timing: {(end - start) / 60} min')
        return result
    return timed


def create_finops_role():
    """ Create a finops role and grant needed permissions. """
    admin_cfn = boto3.client('cloudformation')
    admin_iam = boto3.client('iam')

    logger.info('As admin creating role for Finops')
    role_arn = admin_iam.create_role(
        Path='/',
        RoleName='TestFinopsRole',
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{account_id}:root" },
                    "Action": "sts:AssumeRole",
                }
            ]
        }),
        Description='string'
    )['Role']['Arn']
    admin_iam.put_role_policy(
        RoleName='TestFinopsRole',
        PolicyName='finops-access-to-bucket-with-cfn',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "ReadTestBucket",
                    "Effect": "Allow",
                    "Action": [
                        "s3:List*",
                        "s3:Get*"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{account_id}-cid-tests-deleteme",
                        f"arn:aws:s3:::{account_id}-cid-tests-deleteme/*"
                    ]
                },
            ]
        }),
    )
    logger.info('Role Created %s', role_arn)

    logger.info('As admin creating permissions for Finops')
    admin_cfn.create_stack(
        StackName="cid-admin",
        TemplateURL=upload_to_s3('cfn-templates/cid-admin-policies.yaml'),
        Parameters=[
            {"ParameterKey": 'RoleName', "ParameterValue":'TestFinopsRole'},
            {"ParameterKey": 'QuickSightManagement', "ParameterValue":'no'},
            {"ParameterKey": 'QuickSightAdmin', "ParameterValue":'no'},
            {"ParameterKey": 'CloudIntelligenceDashboardsCFNManagement', "ParameterValue":'yes'},
            {"ParameterKey": 'CURDestination', "ParameterValue":'yes'},
            {"ParameterKey": 'CURReplication', "ParameterValue":'no'},
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
    )
    watch_stacks(admin_cfn, ["cid-admin"])
    logger.info('Stack created')


def create_cid_as_finops():
    """creates cid with finops role"""
    admin_cfn = boto3.client('cloudformation')

    logger.info('Logging is as Finops person')
    credentials = boto3.client('sts').assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/TestFinopsRole" ,
        RoleSessionName="FinopsPerson"
    )['Credentials']
    finops_session = boto3.session.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    logger.info('Finops Session created')

    logger.info('As Finops Creating CUR')
    finops_cfn = finops_session.client('cloudformation')
    finops_cfn.create_stack(
        StackName="CID-CUR-Destination",
        TemplateURL=upload_to_s3('cfn-templates/cur-aggregation.yaml'),
        Parameters=[
            {"ParameterKey": 'DestinationAccountId', "ParameterValue": account_id},
            {"ParameterKey": 'ResourcePrefix', "ParameterValue": 'cid'},
            {"ParameterKey": 'CreateCUR', "ParameterValue": 'True'},
            {"ParameterKey": 'SourceAccountIds', "ParameterValue": ''},
        ],
        Capabilities=['CAPABILITY_IAM'],
    )
    watch_stacks(admin_cfn, ["CID-CUR-Destination"])
    logger.info('Stack created')

    logger.info('As Finops Creating Dashboards')
    res = finops_cfn.create_stack(
        StackName="Cloud-Intelligence-Dashboards",
        TemplateURL=upload_to_s3('cfn-templates/cid-cfn.yml'),
        Parameters=[
            {"ParameterKey": 'PrerequisitesQuickSight', "ParameterValue": 'yes'},
            {"ParameterKey": 'PrerequisitesQuickSightPermissions', "ParameterValue": 'yes'},
            {"ParameterKey": 'QuickSightUser', "ParameterValue": get_qs_user()},
            {"ParameterKey": 'DeployCUDOSDashboard', "ParameterValue": 'yes'},
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
    )
    logger.debug(res)
    watch_stacks(admin_cfn, ["Cloud-Intelligence-Dashboards"])
    logger.info('Stack created')


def test_dashboard_exists():
    """check that dashboard exists"""
    dash = boto3.client('quicksight').describe_dashboard(
        AwsAccountId=account_id,
        DashboardId='cudos'
    )['Dashboard']
    logger.info("Dashboard exists with status = %s", dash['Version']['Status'])


def test_dataset_scheduled():
    """check that dataset and schedule exist"""
    schedules = boto3.client('quicksight').list_refresh_schedules(AwsAccountId=account_id, DataSetId='d01a936f-2b8f-49dd-8f95-d9c7130c5e46')['RefreshSchedules']
    if not schedules:
        raise Exception('Schedules not set') #pylint: disable=broad-exception-raised

def test_ingestion_successful():
    """check that first ingestion is successful"""
    qs = boto3.client('quicksight')

    timeout_seconds = 300
    dataset_name = 'summary_view' # Please note that there can be already another dataset in with the same name

    logger.info('Waiting for the first ingestion')
    dataset_id = None
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        datasets = {}
        for dst in  qs.list_data_sets(AwsAccountId=account_id)['DataSetSummaries']:
            datasets[dst["Name"]]= dst["DataSetId"]
        if dataset_name in datasets:
            dataset_id = datasets[dataset_name]
            break
        time.sleep(2)
    else:
        raise AssertionError('Timeout while waiting for dataset')

    logger.info('Waiting for the first ingestion results')
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        ingestions = qs.list_ingestions(AwsAccountId=account_id, DataSetId=dataset_id)['Ingestions']
        if not ingestions:
            time.sleep(2)
            continue
        latest = sorted(ingestions, key=lambda x: x['CreatedTime'])[-1]
        logger.debug(latest['IngestionStatus'])
        if latest['IngestionStatus'] == 'FAILED':
            raise AssertionError(f"ingestion of dataset {dataset_name} FAILED: {latest['ErrorInfo']}")
        elif latest['IngestionStatus'] == 'COMPLETED':
            logger.info('Ingestion Successful')
            logger.debug(latest)
            break
    else:
        raise AssertionError(f'Timeout while waiting for {dataset_name} dataset ingestion.')


def teardown():
    """Cleanup the test"""
    admin_cfn = boto3.client('cloudformation')
    admin_iam = boto3.client('iam')

    logger.info('Logging is as Finops person')
    credentials = boto3.client('sts').assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/TestFinopsRole" ,
        RoleSessionName="FinopsPerson"
    )['Credentials']
    finops_session = boto3.session.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    logger.info('Finops Session created')

    finops_cfn = finops_session.client('cloudformation')

    logger.info("Deleting bucket")
    delete_bucket(f'cid-{account_id}-shared') # Cannot be done by CFN
    logger.info("Deleting Dashboards stack")
    try:
        finops_cfn.delete_stack(StackName="Cloud-Intelligence-Dashboards")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.info(exc)
    logger.info("Deleting CUR stack")
    try:
        finops_cfn.delete_stack(StackName="CID-CUR-Destination")
    except Exception as exc: # pylint: disable=broad-exception-caught
        logger.info(exc)
    logger.info("Deleting Admin stack")
    watch_stacks(admin_cfn, ["Cloud-Intelligence-Dashboards", "CID-CUR-Destination"])

    try:
        admin_cfn.delete_stack(StackName="cid-admin")
    except Exception as exc: # pylint: disable=broad-exception-caught
        logger.info(exc)
    logger.info("Waiting for all deletions to complete")
    watch_stacks(admin_cfn, ["cid-admin"])

    logger.info("Delete role")
    try:
        for policy in admin_iam.list_role_policies(RoleName='TestFinopsRole')['PolicyNames']:
            admin_iam.delete_role_policy(RoleName='TestFinopsRole', PolicyName=policy)
        admin_iam.delete_role(RoleName='TestFinopsRole')
    except Exception as exc: # pylint: disable=broad-exception-caught
        logger.info(exc)

    logger.info("Cleanup tmp bucket")
    delete_bucket(f'{account_id}-cid-tests-deleteme')
    logger.info("Teardown done")


@timeit
def main():
    """ main """
    try:
        try:
            teardown() #Try to remove previous attempt
        except Exception as exc: # pylint: disable=broad-exception-caught
            logger.debug(exc)
        create_finops_role()
        create_cid_as_finops()
        test_dashboard_exists()
        test_dataset_scheduled()
        test_ingestion_successful()
    except Exception as exc:
        logger.error(exc)
        raise
    finally:
        for index in range(10):
            print(f'Press Ctrl+C if you want to avoid teardown: {9-index}\a') # beep
            time.sleep(1)
        teardown()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
