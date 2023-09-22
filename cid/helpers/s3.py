import json
import logging
import botocore

from cid.base import CidBase, CidException

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
                raise CidException(f"Cannot check bucket {ex}!")
            
            response = self.client.create_bucket(
                ACL='private',
                Bucket=name
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
