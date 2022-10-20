import logging

from cid.commands.command_base import Command


class InitCommand(Command):
    def __init__(self, cid, logger=None, **kwargs):
        self.cid = cid
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)
        
    def execute(self):
        """ Execute the initilization """
        print('Initializing AWS environment...')
        print('-------------------------------')
        # Create QuickSight Enterprise subscription
        self._create_quicksight_enterprise_subscription()
        # Create Athena workgroup "cid" + s3 bucket
        # Create table with predefined fields and a crawler that updates it
    
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
            decision = input('\tPlease, confirm that you are OK with this (yes/[no]): ')
            decision = 'no' if decision not in ('yes', 'y') else 'yes'
        else:
            decision = 'yes'
        
        if decision == 'no':
            print('\tInitalization cancelled')
            return
        
        email = ''
        print(f'\n\tQuicksight needs an email address that you want it to send notifications to regarding your Amazon QuickSight account or Amazon QuickSight subscription.')
        while '@' not in email or '.' not in email:
            email = input('\tNotification email: ')
            if '@' not in email or '.' not in email:
                print(f'\t{email} does not seem to be a valid email. Please, try again.')
        
        PARAMS = {
            'Edition': 'ENTERPRISE',
            'AuthenticationMethod': 'IAM_AND_QUICKSIGHT',
            'AwsAccountId': self.cid.base.account_id,
            'AccountName': f'qs-cid-{self.cid.base.account_id}',
            'NotificationEmail': email,
        }
        
        pass
