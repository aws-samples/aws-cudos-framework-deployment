import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class S3(CidBase):

    def __init__(self, session):
        super().__init__(session)
        # QuickSight client
        self.client = self.session.client('s3', region_name=self.region)
        
    def ensure_bucket(self, name: str) -> str:
        try:
            response = self.client.head_bucket(Bucket=name)
            return name
        except Exception as ex:
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
            return name            
