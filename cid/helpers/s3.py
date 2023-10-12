import json
import logging
import botocore
from typing import Optional, List

from cid.base import CidBase
from cid.exceptions import CidError

logger = logging.getLogger(__name__)


class S3(CidBase):

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('s3', region_name=self.region)
        
    def ensure_bucket(self, name: str) -> str:
        try:
            response = self.client.head_bucket(Bucket=name)
            return name
        except botocore.exceptions.ClientError as ex:
            if int(ex.response['Error']['Code']) != 404:
                raise CidError(f"Cannot check bucket {ex}!")
            
            parameters = {
                'ACL': 'private',
                'Bucket': name
            }
            
            if self.region != 'us-east-1':
                parameters.update({'CreateBucketConfiguration': {'LocationConstraint': self.region}})
            
            response = self.client.create_bucket(
                **parameters
            )
            
            response = self.client.put_bucket_encryption(
                Bucket=name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256',
                            },
                        },
                    ]
                }
            )
            
            response = self.client.put_bucket_lifecycle_configuration(
                Bucket=name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'Expiration': {
                                'Days': 14,
                            },
                            'Filter': {
                                'Prefix': '/',
                            },
                            'ID': 'ExpireAfter14Days',
                            'Status': 'Enabled',
                        },
                    ],
                },
            )
            return name            

    def list_buckets(self, region_name: Optional[str] = None) -> List[str]:
        buckets = self.client.list_buckets()
        bucket_regions = {
            x['Name']: self.client.get_bucket_location(Bucket=x['Name']).get('LocationConstraint', None) for x in buckets['Buckets']
        }
        for bucket in bucket_regions:
            if bucket_regions[bucket] is None:
                bucket_regions[bucket] = 'us-east-1'
                
        if region_name:
            bucket_names = [x['Name'] for x in buckets['Buckets'] if bucket_regions.get(x['Name']) == region_name] 
        else:
            bucket_names = [x['Name'] for x in buckets['Buckets']] 
        return bucket_names