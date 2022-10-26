import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class S3(CidBase):

    def __init__(self, session):
        super().__init__(session)
        # QuickSight client
        self.client = self.session.client('s3', region_name=self.region)
    
    def create_bucket(self, bucket_name: str) -> str:
        try:
            response_create = self.client.create_bucket(
                ACL='private',
                Bucket=bucket_name,
                ObjectOwnership='BucketOwnerEnforced'
            )
                
            response_encrypt = self.client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        },
                    ]
                },
            )
            
            response_public = self.client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                },
            )
            
            response_lifecycle = self.client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'Expiration': {
                                'Days': 7
                            },
                            'Filter': {
                                'Prefix': ''
                            },
                            'ID': 'DeleteContent',
                            'Status': 'Enabled'
                        }
                    ]
                }
            )
        
            return bucket_name
        except Exception as ex:
            raise
        
