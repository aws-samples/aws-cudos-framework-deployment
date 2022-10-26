import logging

from cid.commands.command_base import Command
from cid.utils import get_parameter, get_yesno_parameter, unset_parameter


class InitCommand(Command):
    def __init__(self, cid, logger=None, **kwargs):
        self.cid = cid
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)
        
        self.bucket_name = None
        
    def execute(self):
        """ Execute the initilization """
        print('Initializing AWS environment...')
        print('-------------------------------')
        # Create QuickSight Enterprise subscription
        self._create_quicksight_enterprise_subscription()
        # Create query results bucket
        self._create_query_results_bucket()
        # Create Athena workgroup "cid"
        # Create table with predefined fields and a crawler that updates it
    
    def _create_query_results_bucket(self):
        self.bucket_name = f'aws-athena-query-results-cid-{self.cid.base.account_id}-{self.cid.base.region}'
        try:
            self.cid.s3.create_bucket(self.bucket_name)
            print(f'\tAthena S3 Bucket...\tCreated ({self.bucket_name})')
        except Exception as ex:
            print(f'\tAthena S3 Bucket...\tFailed')
            self._logger.error(f'ERROR: {ex}')
    
    def _create_quicksight_enterprise_subscription(self):
        required_editions = {'ENTERPRISE', 'ENTERPRISE_AND_Q'}
        
        if self.cid.qs.edition in required_editions:
            self._logger.info(f'QuickSight Edition: "{self.cid.qs.edition}", nothing to do')
            print('\tQuickSight Edition...\tOK')
            return
            
        self._logger.info(f'QuickSight Edition: "{self.cid.qs.edition}", needs to be in [{", ".join(required_editions)}]')
        print(f'\tQuickSight Edition...\t{self.cid.qs.edition}, needs to be one of {", ".join(required_editions)}')
        print(f'\tIMPORTANT: QuickSight Enterprise is required for Cost Intelligence Dashboard. This will lead to costs in your AWS account (https://aws.amazon.com/quicksight/pricing/).')
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
        print(f'\n\tQuicksight needs an email address that you want it to send notifications to regarding your Amazon QuickSight account or Amazon QuickSight subscription.')
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
        print(f'\n\tPlease, choose a descriptive name for your QuickSight account. This will be used later to share it with your users. This can NOT be changed later.')
        while account_name == '':
            counter += 1
            account_name = get_parameter('qs-account-name', 'QuickSight Account Name', default=account_name)
            if account_name == '':
                print(f'\t The account name must not be empty. Please, try again.')
                unset_parameter('qs-account-name')
                if counter >= 5:
                    exit(1)
        
        PARAMS = {
            'Edition': 'ENTERPRISE',
            'AuthenticationMethod': 'IAM_AND_QUICKSIGHT',
            'AwsAccountId': self.cid.base.account_id,
            'AccountName': account_name,  # Should be a parameter with a reasonable default
            'NotificationEmail': email,  # Read the value from account parameters as a default
        }
        
        response = self.cid.qs.client.create_account_subscription(**PARAMS)
        if response.get('Status', 0) == 200:
            print('\tQuickSight Edition...\tSubscribed')
        pass
