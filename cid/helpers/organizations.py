import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class Organizations(CidBase):

    def __init__(self, session):
        super().__init__(session)
        # QuickSight client
        self.client = self.session.client('organizations', region_name=self.region)
    
    def get_account_email(self):
        try:
            response = self.client.describe_account(AccountId=self.account_id)
            result = response.get('Email', '')
        except Exception as ex:
            result = ''
            
        return result
    
    def get_account_name(self):
        try:
            response = self.client.describe_account(AccountId=self.account_id)
            result = response.get('Name', '')
        except Exception as ex:
            result = ''
            
        return result
