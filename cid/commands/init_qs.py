""" Command Init QuickSight
"""
import logging

from cid.commands.command_base import Command
from cid.exceptions import CidCritical
from cid.utils import (
    get_parameter,
    get_yesno_parameter,
    unset_parameter,
    cid_print,
)

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5


class InitQsCommand(Command):  # pylint: disable=too-few-public-methods
    """Init Command for CLI"""

    def __init__(self, cid, **kwargs):
        self.cid = cid

    def execute(self, *args, **kwargs):
        """Execute the initilization"""
        self._create_quicksight_enterprise_subscription()  # No tagging available


    def _create_quicksight_enterprise_subscription(self):
        """Enable QuickSight Enterprise if not enabled already"""
        cid_print('Analysing QuickSight Status')
        if self.cid.qs.edition in ('ENTERPRISE', 'ENTERPRISE_AND_Q'):
            cid_print(f'QuickSight Edition is {self.cid.qs.edition}')
            return

        cid_print(
            '<BOLD><RED>IMPORTANT<END>: <BOLD>Amazion QuickSight Enterprise Edition is required for Cost Intelligence Dashboard. '
            'This will lead to costs in your AWS account (https://aws.amazon.com/quicksight/pricing/).<END>'
        )
        if not self.cid.all_yes:
            enable_quicksight_enterprise = get_yesno_parameter(
                param_name='enable-quicksight-enterprise', message='Please, confirm enabling of Amazion QuickSight Enterprise', default='no'
            )
        else:
            enable_quicksight_enterprise = True

        if not enable_quicksight_enterprise:
            cid_print('\tInitalization cancelled')
            return

        counter = 0
        while True:
            email = self._get_email_for_quicksight()
            account_name = self._get_account_name_for_quicksight()
            params = self._get_quicksight_params(email, account_name)
            counter += 1
            try:
                response = self.cid.qs.client.create_account_subscription(**params)
                cid_print(f'QuickSight Edition is {response}')
                break
            except Exception as exc: #pylint: disable=broad-exception-caught
                cid_print(f'\tQuickSight Edition...\tError ({exc}). Please, try again or press CTRL + C to interrupt.')
                unset_parameter('qs-account-name')
                unset_parameter('qs-notification-email')
                if counter >= MAX_ITERATIONS:
                    raise CidCritical('Quicksight setup failed') from exc

    def _get_quicksight_params(self, email, account_name):
        """Create dictionary of quicksight subscription initialization parameters"""
        params = {
            'Edition': 'ENTERPRISE',
            'AuthenticationMethod': 'IAM_AND_QUICKSIGHT',
            'AwsAccountId': self.cid.base.account_id,
            'AccountName': account_name,  # Should be a parameter with a reasonable default
            'NotificationEmail': email,  # Read the value from account parameters as a default
        }

        return params

    def _get_account_name_for_quicksight(self):
        """Get the account name for quicksight"""        
        account_name = get_parameter('qs-account-name', 'QuickSight Account Name', default=self.cid.organizations.get_account_name())

        if account_name == '':
            print(
                '\n\tPlease, choose a descriptive name for your QuickSight account. '
                'This will be used later to share it with your users. This can NOT be changed later.'
            )

        counter = 0
        while not account_name or account_name == '':
            counter += 1
            account_name = get_parameter('qs-account-name', 'QuickSight Account Name', default=self.cid.organizations.get_account_name())
            if account_name == '':
                print('\t The account name must not be empty. Please, try again.')
                unset_parameter('qs-account-name')
                if counter >= MAX_ITERATIONS:
                    raise CidCritical('Failed to read QuickSight Account Name')
        return account_name

    def _get_email_for_quicksight(self):
        """Get email for quicksight"""        
        email = get_parameter('qs-notification-email', 'Notification email', default=self.cid.organizations.get_account_email())

        if email == '':
            print(
                '\n\tQuicksight needs an email address that you want it to send notifications to '
                'regarding your Amazon QuickSight account or Amazon QuickSight subscription.'
            )

        counter = 0
        while not email or '@' not in email or '.' not in email:
            counter += 1
            email = get_parameter('qs-notification-email', 'Notification email', default=self.cid.organizations.get_account_email())
            if '@' not in email or '.' not in email:
                print(f'\t{email} does not seem to be a valid email. Please, try again.')
                unset_parameter('qs-notification-email')
                if counter >= MAX_ITERATIONS:
                    raise CidCritical('Failed to read email')
        return email
