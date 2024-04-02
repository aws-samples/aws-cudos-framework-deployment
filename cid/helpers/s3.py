import re
import logging
from typing import Optional, List

from cid.base import CidBase
from cid.exceptions import CidError


logger = logging.getLogger(__name__)


class S3(CidBase):
    ''' S3 Helper
    '''
    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('s3', region_name=self.region)

    def ensure_bucket(self, name: str, lifecycle: int=14) -> str:
        ''' ensure bucket exists, have an encryption and lifecycle
        '''
        try:
            self.client.head_bucket(Bucket=name)
            return name
        except self.client.exceptions.ClientError as exc:
            if int(exc.response['Error']['Code']) != 404:
                raise CidError(f"Cannot check bucket {exc}!") from exc

        parameters = {
            'ACL': 'private',
            'Bucket': name
        }
        if self.region != 'us-east-1':
            parameters['CreateBucketConfiguration'] = {'LocationConstraint': self.region}
        self.client.create_bucket(**parameters)

        self.client.put_bucket_encryption(
            Bucket=name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                        'ApplyServerSideEncryptionByDefault': { 'SSEAlgorithm': 'AES256' },
                }]
            }
        )

        if lifecycle is not None:
            self.client.put_bucket_lifecycle_configuration(
                Bucket=name,
                LifecycleConfiguration={
                    'Rules': [{
                        'ID': 'ExpireAfter14Days',
                        'Status': 'Enabled',
                        'Expiration': { 'Days': lifecycle },
                        'Filter': { 'Prefix': '/' },
                    }],
                },
            )
        return name

    def list_buckets(self, region_name: Optional[str] = None) -> List[str]:
        ''' List buckets
        region_name: optional region filter
        '''
        bucket_names = [bucket['Name'] for bucket in self.client.list_buckets()['Buckets']]
        if region_name:
            bucket_names = list(filter(
                lambda bucket_name: self.client.get_bucket_location(Bucket=bucket_name).get('LocationConstraint', 'us-east-1') == region_name,
                bucket_names,
            ))
        return bucket_names

    def iterate_objects(self, bucket: str, prefix: str='/', search: str='Contents[].Key') -> List[str]:
        ''' iterate objects in bucket
        '''
        yield from self.client.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix).search(search)

    def list_path_prefixes_with_regexp(self, bucket: str, regexp: str, prefix: str='/') -> List[str]:
        ''' list prefixes of bucket object keys before given regexp
        bucket: bucket name
        regexp: a regexp that should match. ex : 'year*/month*/'
        '''
        paths = []
        regexp = regexp.replace('*', '.+?') + '$'
        for key in self.iterate_objects(bucket=bucket):
            path = '/'.join(key.split('/')[:-1]) + '/'
            if any(path.startswith(existing_path) for existing_path in paths):
                continue # not original prefix
            if re.findall(regexp, path):
                paths.append(re.sub(regexp,'',path))
        return paths
