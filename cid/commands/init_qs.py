""" Command Init QuickSight
"""
import re
import time
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
        """Execute the initialization"""
        self._create_quicksight_enterprise_subscription()

    def _create_quicksight_enterprise_subscription(self):
        """Enable QuickSight Enterprise if not enabled already"""
        cid_print('Analyzing QuickSight Status')
        if self.cid.qs.edition(fresh=True) in ('ENTERPRISE', 'ENTERPRISE_AND_Q'):
            cid_print(f'QuickSight Edition is {self.cid.qs.edition()}')
            return

        cid_print(
            '<BOLD><RED>IMPORTANT<END>: <BOLD>Amazon QuickSight Enterprise Edition is required for Cloud Intelligence Dashboards. '
            'Enabling Amazon QuickSight Enterprise Edition will incur associated service charges. Make sure you aware about them following QuickSight pricing page (https://aws.amazon.com/quicksight/pricing/) and acknowledge by confirming enabling it. Alternatively you can enable QuickSight Enterprise Edition in the AWS console (https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html) and run this command again.<END>'
        )

        if not self.cid.all_yes and not get_yesno_parameter(
                param_name='enable-quicksight-enterprise',
                message='Please, confirm enabling of Amazon QuickSight Enterprise',
                default='no'
            ):
            cid_print('\tInitialization cancelled')
            return

        for counter in range(MAX_ITERATIONS):
            email = self._get_email_for_quicksight()
            account_name = self._get_account_name_for_quicksight()
            params = {
                'Edition': 'ENTERPRISE',
                'AuthenticationMethod': 'IAM_AND_QUICKSIGHT',
                'AwsAccountId': self.cid.base.account_id,
                'AccountName': account_name,
                'NotificationEmail': email,
            }
            cid_print('Initializing Amazon QuickSight in your AWS Account')
            try:
                response = self.cid.qs.client.create_account_subscription(**params)
                logger.debug(f'create_account_subscription resp: {response}')
                if response.get('Status') != 200:
                    raise CidCritical(f'Subscription answer is not 200: {response}')
                break
            except Exception as exc: #pylint: disable=broad-exception-caught
                cid_print(f'\tQuickSight Edition...\tError ({exc}). Please, try again or press CTRL + C to interrupt.')
                unset_parameter('account-name')
                unset_parameter('notification-email')
                if counter == MAX_ITERATIONS - 1:
                    raise CidCritical('Quicksight setup failed') from exc
        while self.cid.qs.edition(fresh=True) not in ('ENTERPRISE', 'ENTERPRISE_AND_Q'):
            time.sleep(5)
        cid_print(f'\tQuickSight Edition is {self.cid.qs.edition()}.')

    def _get_account_name_for_quicksight(self):
        """Get the account name for quicksight"""
        for _ in range(MAX_ITERATIONS):
            cid_print('Please, choose a descriptive name for your QuickSight account.')
            cid_print('This will be used later to share it with your users. For test you can use AWS Account Id. This can NOT be changed later. If you are planning to use IdC stop now and create QuickSight Account in UI.')
            account_name = get_parameter(
                'account-name',
                message='Please enter a unique name [A-Za-z0-9-]',
                default=self.cid.organizations.get_account_name()
            )
            if not re.match('[A-Za-z0-9-]', account_name):
                logger.error('account_name must match [A-Za-z0-9-]')
                unset_parameter('account-name')
                continue
            if account_name:
                return account_name
            print('\t The account name must not be empty. Please, try again.')
            unset_parameter('account-name')
        else: #pylint: disable=W0120:useless-else-on-loop
            raise CidCritical('Failed to read QuickSight Account Name')


    def _get_email_for_quicksight(self):
        """Get email for quicksight"""
        for _ in range(MAX_ITERATIONS):
            email = get_parameter(
                'notification-email',
                message=(
                    'Amazon QuickSight needs your email address to send notifications '
                    'regarding your Amazon QuickSight account.'
                ),
                default=self.cid.organizations.get_account_email()
            )
            if '@' in email and '.' in email:
                return email
            cid_print(f'\t{email} does not seem to be a valid email. Please, try again.')
            unset_parameter('notification-email')
        else: #pylint: disable=W0120:useless-else-on-loop
            raise CidCritical('Failed to read email')
