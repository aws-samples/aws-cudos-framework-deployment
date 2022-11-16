import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class S3(CidBase):
    """ S3 helper class """
    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('s3', region_name=self.region)

    def create_bucket(self, bucket_name: str) -> str:
        """ Create a bucket with the specified name """
        self.client.create_bucket(
            ACL='private',
            Bucket=bucket_name,
            ObjectOwnership='BucketOwnerEnforced'
        )

        self.client.put_bucket_encryption(
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

        self.client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            },
        )

        self.client.put_bucket_lifecycle_configuration(
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
