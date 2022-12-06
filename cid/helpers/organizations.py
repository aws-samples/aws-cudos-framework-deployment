import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class Organizations(CidBase):
    """Organizations helper class"""

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client("organizations", region_name=self.region)

    def get_account_email(self):
        """Try to extract the account's email address for Organizations"""
        try:
            result = self.client.describe_account(AccountId=self.account_id).get("Email", "")
        except Exception:  # pylint: disable=broad-except
            result = None

        return result

    def get_account_name(self):
        """Try to extract the account name from Organizations"""
        try:
            result = self.client.describe_account(AccountId=self.account_id).get("Name", "")
        except Exception:  # pylint: disable=broad-except
            result = None

        return result
