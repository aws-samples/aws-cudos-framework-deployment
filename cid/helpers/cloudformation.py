""" CloudFormation Helper
"""
import logging
from functools import lru_cache

from cid.base import CidBase

logger = logging.getLogger(__name__)


class CFN(CidBase):

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('cloudformation', region_name=self.region)

    @lru_cache(1000)
    def get_read_access_policies(self):
        ''' returns a dict of read access policies provided by other stacks

        data collection stack can add CFN export ReadAccessPolicyARN

        return example:
            {
                "cid-DataCollection-ReadAccessPolicyARN": "arn:aws:iam::xxx:policy/CID-DC-DataCollectionReadAccess",
                "cid-DataExports-ReadAccessPolicyARN": "arn:aws:iam::xxx:policy/cidDataExportsReadAccess",
                "cid-SecurityHub-ReadAccessPolicyARN": "arn:aws:iam::xxx:policy/cid-SecurityHubReadAccess"
            }
        '''
        try:
            res = dict(
                self.client
                    .get_paginator('list_exports')
                    .paginate()
                    .search("Exports[? starts_with(Name, 'cid-') && ends_with(Name,'ReadAccessPolicyARN')][Name, Value]"
                )
            )
        except self.client.exceptions.ClientError as exc:
            if 'AccessDenied' in str(exc):
                logger.warning('AccessDenied on cloudformation:ListExports. Most likely not critical.')
                res = {}
            else:
                raise
        return  res

    @lru_cache(1000)
    def get_read_access_policy(self, key):
        ''' return a list of read access policies provided by other stacks
        key: cfn export name
        '''
        return  self.get_read_access_policies().get(key, None)

    @lru_cache(1000)
    def get_read_access_policy_for_module(self, module):
        ''' return a list of read access policies provided by other stacks
        module: module name (DataCollection DataExports or SecurityHub)
        '''
        return  self.get_read_access_policy(f'cid-{module}-ReadAccessPolicyARN')
