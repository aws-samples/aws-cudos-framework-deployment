import importlib.resources as pkg_resources
import logging
import sys

from cid.commands.command_base import Command
from cid.utils import (extract_cur_bucket_parameters, get_parameter,
                       get_yesno_parameter, unset_parameter)


class InitCommand(Command):  # pylint: disable=too-few-public-methods
    """ Init Command for CLI """
    def __init__(self, cid, logger=None, **kwargs):
        self.cid = cid
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)

        self.bucket_name = f'aws-athena-query-results-cid-{self.cid.base.account_id}-{self.cid.base.region}'
        self.athena_workgroup_name = 'cid'
        self.database_name = 'cid_cur'
        self.catalog_id = self.cid.base.account_id
        self.cur_path = f's3://cid-{self.cid.base.account_id}-shared/cur/'
        self.cid_crawler_role_name = 'CidCURCrawlerRole'
        self.cid_crawler_role_arn = ''
        self.aws_partition = 'aws'
        self.processed_cur_path = None

    def execute(self, *args, **kwargs):
        """ Execute the initilization """
        print('Initializing AWS environment...')
        print('-------------------------------')
        # Collect partition and CUR bucket path
        self._get_base_data()
        # Create QuickSight Enterprise subscription
        self._create_quicksight_enterprise_subscription()
        # Create query results bucket
        self._create_query_results_bucket()
        # Create Athena workgroup "cid"
        self._create_athena_workgroup()
        # Create Glue database
        self._create_glue_database()
        # Create table with predefined fields
        self._create_glue_crawler_role()
        self._attach_policies_to_crawler_role()

        self._create_glue_crawler()
        # self._create_glue_table()
        # Create crawler that updates the table

    def _get_base_data(self):
        self.aws_partition = get_parameter('aws-partition', 'Please, choose an AWS partition', choices=['aws', 'aws-cn'], default='aws')
        self.cur_path = get_parameter('cur-path', 'Please, provide your CUR path', default=self.cur_path)
        self.processed_cur_path = extract_cur_bucket_parameters(self.cur_path)

    def _create_glue_crawler_role(self):
        """ Create IAM role for Glue crawler """
        self.cid_crawler_role_arn = get_parameter('glue-role-arn', 'Glue role ARN. Hit ENTER to create new role', default='')

        if self.cid_crawler_role_arn != '':
            print(f'\tGlue role ARN...\tProvided ({self.cid_crawler_role_arn})')
        try:
            assume_role_policy_document = pkg_resources.read_text('cid.builtin.core.data.iam', 'glue_assume_role_policy_document.json')
        except Exception:  # pylint: disable=broad-except
            self._logger.exception()
            print('\tGlue role ARN...\tERROR: Could not load role policy document')

        try:
            self.cid_crawler_role_arn = self.cid.iam.create_role(
                role_name=self.cid_crawler_role_name,
                assume_role_policy_document=assume_role_policy_document
            )
            print(f'\tGlue role ARN...\tCreated ({self.cid_crawler_role_arn})')
        except Exception:  # pylint: disable=broad-except
            self._logger.debug("WARNING: Cannot create glue role")
            self.cid_crawler_role_arn = self.cid.iam.get_role_arn(role_name=self.cid_crawler_role_name)
            print(f'\tGlue role ARN...\tExists ({self.cid_crawler_role_arn})')

    def _attach_policies_to_crawler_role(self):
        MANAGED_POLICIES = [
            f'arn:{self.aws_partition}:iam::aws:policy/service-role/AWSGlueServiceRole'
        ]
        CUSTOM_POLICIES = {
            'AWSCURCrawlerComponentFunction': 'aws_cur_crawler_component_function.json',
            'AWSCURKMSDecryption': 'aws_cur_kms_decryption.json'
        }

        print('\tAttaching policies...')
        for policy in MANAGED_POLICIES:
            print(f'\t\t{policy}')
            self.cid.iam.attach_policy(role_name=self.cid_crawler_role_name, policy_arn=policy)

        variables = {
            '${AWS::Region}': self.cid.base.region,
            '${AWS::Partition}': self.aws_partition,
            '${AWS::AccountId}': self.cid.base.account_id,
            '${CidCURDatabase}': self.database_name,
            '${ProcessedCURPath.Bucket}': self.processed_cur_path['Bucket'],
            '${ProcessedCURPath.Path}': self.processed_cur_path['Path']
        }
        for name, policy_file in CUSTOM_POLICIES.items():
            policy_document = pkg_resources.read_text('cid.builtin.core.data.iam', policy_file)
            for key, value in variables.items():
                policy_document = policy_document.replace(key, value)

            try:
                policy = self.cid.iam.create_policy_from_json(policy_name=name, policy_document=policy_document)
            except Exception:  # pylint: disable=broad-except
                policy = f'arn:{self.aws_partition}:iam::{self.cid.base.account_id}:policy/{name}'
            print(f'\t\t{policy}')
            self.cid.iam.attach_policy(role_name=self.cid_crawler_role_name, policy_arn=policy)

    def _create_glue_crawler(self):
        """ Create a new Glue crawler """

    def _create_glue_database(self):
        """ Create Glue database """
        try:
            self.cid.glue.create_database(name=self.database_name, catalog_id=self.catalog_id)
            print(f'\tGlue Database...\tCreated ({self.database_name} in {self.catalog_id})')
        except self.cid.glue.client.exceptions.AlreadyExistsException:
            print(f'\tGlue Database...\tExists ({self.database_name} in {self.catalog_id})')
        except Exception as ex:  # pylint: disable=broad-except
            self._logger.exception(str(ex))
            print('\tGlue Database...\tFailed')

    def _create_athena_workgroup(self):
        """ Create Athena workgroup """
        try:
            self.cid.athena.create_workgroup(workgroup_name=self.athena_workgroup_name, s3_bucket_name=self.bucket_name)
            print(f'\tAthena Workgroup...\tCreated ({self.athena_workgroup_name})')
        except self.cid.athena.WorkGroupAlreadyExistsException:
            print(f'\tAthena Workgroup...\tExists ({self.athena_workgroup_name})')
        except Exception as ex:  # pylint: disable=broad-except
            self._logger.exception(str(ex))
            print('\tAthena Workgroup...\tFailed')

    def _create_query_results_bucket(self):
        """ Create bucket for storing query results """
        try:
            self.cid.s3.create_bucket(self.bucket_name)
            print(f'\tAthena S3 Bucket...\tCreated ({self.bucket_name})')
        except Exception as ex:  # pylint: disable=broad-except
            print('\tAthena S3 Bucket...\tFailed')
            self._logger.error('ERROR: %s', ex)

    def _create_quicksight_enterprise_subscription(self):
        """ Enable QuickSight Enterprise if not enabled already """
        required_editions = {'ENTERPRISE', 'ENTERPRISE_AND_Q'}

        if self.cid.qs.edition in required_editions:
            self._logger.info('QuickSight Edition: "%s", nothing to do', self.cid.qs.edition)
            print('\tQuickSight Edition...\tOK')
            return

        self._logger.info('QuickSight Edition: "%s", needs to be in [%s]', self.cid.qs.edition, ", ".join(required_editions))
        print(f'\tQuickSight Edition...\t{self.cid.qs.edition}, needs to be one of {", ".join(required_editions)}')
        print('\tIMPORTANT: QuickSight Enterprise is required for Cost Intelligence Dashboard. '
              'This will lead to costs in your AWS account (https://aws.amazon.com/quicksight/pricing/).')
        if not self.cid.all_yes:
            enable_quicksight_enterprise = get_yesno_parameter(
                param_name='enable-quicksight-enterprise',
                message='Please, confirm that you are OK with enabling QuickSight Enterprise',
                default='no'
            )
        else:
            enable_quicksight_enterprise = True

        if not enable_quicksight_enterprise:
            print('\tInitalization cancelled')
            return

        email = self.cid.organizations.get_account_email()
        print('\n\tQuicksight needs an email address that you want it to send notifications to '
              'regarding your Amazon QuickSight account or Amazon QuickSight subscription.')
        counter = 0
        while '@' not in email or '.' not in email:
            counter += 1
            email = get_parameter('qs-notification-email', 'Notification email', default=email)
            if '@' not in email or '.' not in email:
                print(f'\t{email} does not seem to be a valid email. Please, try again.')
                unset_parameter('qs-notification-email')
                if counter >= 5:
                    exit(1)

        account_name = self.cid.organizations.get_account_name()
        counter = 0
        print('\n\tPlease, choose a descriptive name for your QuickSight account. '
              'This will be used later to share it with your users. This can NOT be changed later.')
        while account_name == '':
            counter += 1
            account_name = get_parameter('qs-account-name', 'QuickSight Account Name', default=account_name)
            if account_name == '':
                print('\t The account name must not be empty. Please, try again.')
                unset_parameter('qs-account-name')
                if counter >= 5:
                    sys.exit(1)

        params = {
            'Edition': 'ENTERPRISE',
            'AuthenticationMethod': 'IAM_AND_QUICKSIGHT',
            'AwsAccountId': self.cid.base.account_id,
            'AccountName': account_name,  # Should be a parameter with a reasonable default
            'NotificationEmail': email,  # Read the value from account parameters as a default
        }

        response = self.cid.qs.client.create_account_subscription(**params)
        if response.get('Status', 0) == 200:
            print('\tQuickSight Edition...\tSubscribed')
