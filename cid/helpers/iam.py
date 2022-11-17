import json
import logging
from pkg_resources import resource_string

from mako.template import Template

from cid.base import CidBase
from cid.exceptions import CidError

logger = logging.getLogger(__name__)

class IAM(CidBase):
    ''' IAM helper

    Permissions:
        iam:ListAttachedRolePolicies
        iam:AttachRolePolicy
        iam:CreatePolicy
        iam:CreatePolicyVersion
        iam:ListPolicyVersions
        iam:DeletePolicyVersion
        iam:GetPolicyVersion
        iam:GetPolicy
        iam:GetRole
        iam:CreateRole
    '''
    def __init__(self, session, resources=None) -> None:
        super().__init__(session)
        self._resources = resources
        self.client = self.session.client('iam')

    def ensure_policy_exists(self, template_file, policy_name, **params):
        ''' Create or update policy
        '''
        template = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=template_file,
        ).decode('utf-8'))
        text = template.render(**params)

        try:
            doc = json.loads(text)
        except Exception as exc:
            raise CidError(f'Error while parsing json. please check template {template_file} and data {params}')
        logger.debug(f'Doc={json.dumps(text)}')
        try:
            arn = self.client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=text
            )['Policy']['Arn']
            logger.debug ('Policy created. arn =', arn )
        except self.client.exceptions.EntityAlreadyExistsException as exc:
            arn = f'arn:aws:iam::{self.account_id}:policy/{policy_name}'
            logger.debug(f'Policy exists. Arn must be={arn}')
            version = self.client.get_policy(PolicyArn=arn)['Policy']['DefaultVersionId']
            current_doc = self.client.get_policy_version(PolicyArn=arn, VersionId=version)['PolicyVersion']['Document']
            if doc != current_doc:
                logger.debug('Updating policy')
                # A managed policy can have up to 5 versions.
                # Before you create a new version, you must delete an existing version.
                versions = self.client.list_policy_versions(PolicyArn=arn)['Versions']
                if len(versions) == 5:
                    for v in versions[::-1]:
                        if not v['IsDefaultVersion']: 
                           self.client.delete_policy_version(PolicyArn=arn, VersionId=v['VersionId'])
                           break
                try:
                    self.client.create_policy_version(PolicyArn=arn, PolicyDocument=text, SetAsDefault=True)
                except self.client.exceptions.LimitExceededException as exc:
                    raise
            else:
                logger.debug(f'no changes')
        return arn


    def ensure_role_exists(self, template_file, role_name, policies):
        ''' Create or update role
        '''
        assume_doc = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=template_file,
        ).decode('utf-8'))

        try:
            role = self.client.get_role(RoleName=role_name)['Role']
        except self.client.exceptions.NoSuchEntityException:
            try:
                role = self.client.create_role(
                    RoleName=role_name,
                    Path='/cid/',
                    AssumeRolePolicyDocument=assume_doc.render(),
                )['Role']
                logger.debug(f'Created role: {role}')
            except iam.exceptions.EntityAlreadyExistsException as exc:
                pass
            except iam.exceptions.AccessDeniedException:
                logger.error('Insufficient permissions. Please addd iam:CreateRole ')

        attach_policies = {p['PolicyName']:p['PolicyArn'] for p in self.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']}
        for policy_name, policy_arn in policies.items():
            if policy_name in attach_policies:
                continue
            self.client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        return role

    def ensure_data_source_role_exists(self, role_name, services=[], buckets=[]):
        ''' Create or update a role for QS Datasource
        '''
        policies = {
            'AWSQuicksightAthenaAccess': 'arn:aws:iam::aws:policy/service-role/AWSQuicksightAthenaAccess'
        }
        for bucket in buckets:
            policies['AWSQuicksightS3-{bucket}'] = self.ensure_policy_exists(
                template_file=f'data/iam/policy-read-s3bucket.json',
                policy_name=f'CidCurBucketPolicy-{bucket}',
                bucket_name=bucket,
            )

        return self.ensure_role_exists(
            template_file = 'data/iam/datasource-role.json',
            role_name = role_name,
            policies = policies
        )

def test_create_delete():
    import boto3
    iam = IAM(boto3.session.Session())
    role_name = 'test_role'
    role = iam.ensure_data_source_role_exists(role_name, buckets=['aaa'])
    assert role

    attach_policies = { p['PolicyName']:p['PolicyArn']
        for p in iam.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    }
    assert 'AWSQuicksightAthenaAccess' in attach_policies

    for i in range(10):
        role = iam.ensure_data_source_role_exists(role_name, buckets=[f'aaa{i}'])
    assert role



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    test_create_delete()