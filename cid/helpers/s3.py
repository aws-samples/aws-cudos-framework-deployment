import logging

from cid.base import CidBase
from cid.exceptions import CidCritical, CidError

logger = logging.getLogger(__name__)


class S3(CidBase):
    """ S3 helper class """
    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('s3', region_name=self.region)

    def create_bucket(self, bucket_name: str, athena_bucket_lifecycle_expiration: int) -> str:
        """ Create a bucket with the specified name """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            raise CidError('Exists')
        except self.client.exceptions.ClientError as ex:
            if ex.response['Error']['Code'] == '403':
                raise CidCritical('You are not authorized to use this bucket') from ex
            pass
        
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
                            'Days': athena_bucket_lifecycle_expiration
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
