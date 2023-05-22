import json
import logging
from pkg_resources import resource_string

import boto3
from mako.template import Template

from cid.base import CidBase
from cid.exceptions import CidError

logger = logging.getLogger(__name__)

class IAM(CidBase):
    ''' IAM helper
    '''
    permissions = '''
        iam:ListAttachedRolePolicies
        iam:AttachRolePolicy
        iam:DetachRolePolicy
        iam:CreateRole
        iam:GetRole
        iam:DeleteRole
        iam:CreatePolicy
        iam:DeletePolicy
        iam:GetPolicy
        iam:CreatePolicyVersion
        iam:DeletePolicyVersion
        iam:GetPolicyVersion
        iam:ListPolicyVersions
    '''.split()

    def __init__(self, session, resources=None) -> None:
        super().__init__(session)
        self._resources = resources
        self.client = self.session.client('iam')

    def ensure_policy_exists(self, template_file, policy_name, **params):
        ''' Create or update policy
        If policy exists, it also merges the policy document on resource level
        '''
        template = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=template_file,
        ).decode('utf-8'))
        text = template.render(**params)

        #Fail fast if json is not well formatted
        try:
            doc = json.loads(text)
        except Exception as exc:
            raise CidError(f'Error while parsing json. please check template {template_file} and data {params}')
        logger.debug(f'Doc={json.dumps(doc)}')

        try:
            arn = self.client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=text
            )['Policy']['Arn']
            logger.debug(f'Policy created. arn = {arn}')
        except self.client.exceptions.EntityAlreadyExistsException as exc:
            arn = f'arn:aws:iam::{self.account_id}:policy/{policy_name}'
            logger.debug(f'Policy exists. Arn must be={arn}')
            version = self.client.get_policy(PolicyArn=arn)['Policy']['DefaultVersionId']
            current_doc = self.client.get_policy_version(
                PolicyArn=arn,
                VersionId=version
            )['PolicyVersion']['Document']
            if doc != current_doc:
                result_doc = merge_policy_docs_on_resource_level(current_doc, doc)
                json_doc = json.dumps(result_doc)
                logger.debug(f'Updating policy {arn} to {result_doc}')
                # A managed policy can have up to 5 versions.
                # Before you create a new version, you must delete an existing version.
                versions = self.client.list_policy_versions(PolicyArn=arn)['Versions']
                if len(versions) == 5:
                    for version in versions[::-1]:
                        if not version['IsDefaultVersion']:
                            self.client.delete_policy_version(
                                PolicyArn=arn,
                                VersionId=version['VersionId']
                            )
                            break
                self.client.create_policy_version(PolicyArn=arn, PolicyDocument=json_doc, SetAsDefault=True)
            else:
                logger.debug(f'No changes in {arn}')
        return arn

    def ensure_role_exists(self, template_file, role_name, policies):
        """ Create or update role
        """
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
                    AssumeRolePolicyDocument=assume_doc.render()
                )['Role']
                logger.debug(f'Created role: {role}')
            except self.client.exceptions.EntityAlreadyExistsException as exc:
                pass #TODO: update AssumeDoc if needed
        except self.client.exceptions.ClientError as exc:
            if '(AccessDenied)' in str(exc):
                logger.info(f'Insufficient permissions for IAM. Please addd: {", ".join(self.permissions)}')
            else:
                raise

        attached_policy_arns = []
        # We cannot have more than 10 policy attached to a role but let's make CodeGuru happy
        for page in self.client.get_paginator('list_attached_role_policies').paginate(RoleName=role_name):
            for p in page['AttachedPolicies']:
                attached_policy_arns.append(p['PolicyArn'])

        for policy_arn in policies:
            if policy_arn in attached_policy_arns:
                continue
            self.client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        return role

    def ensure_data_source_role_exists(self, role_name, services=['Athena'], buckets=[]):
        ''' Create or update a role specifically for a QS Datasource
        '''
        policies = []
        if 'Athena' in services:
            policies.append('arn:aws:iam::aws:policy/service-role/AWSQuicksightAthenaAccess')
        for bucket in buckets:
            arn = self.ensure_policy_exists(
                template_file=f'data/iam/policy-read-s3bucket.json',
                policy_name=f'CidQuicksightBucketAccess',
                bucket_name=bucket,
            )
            policies.append(arn)

        return self.ensure_role_exists(
            template_file = 'data/iam/datasource-role.json',
            role_name = role_name,
            policies = list(set(policies)),
        )

    def ensure_role_does_not_exist(self, role_name):
        """ Remove a role and all policies if they are not used in other roles
        """
        try:
            role = self.client.get_role(RoleName=role_name)
        except self.client.exceptions.NoSuchEntityException:
            logger.debug(f'No role {role_name}')
            return

        for page in self.client.get_paginator('list_attached_role_policies').paginate(RoleName=role_name):
            logger.debug(f'page {page}')
            for pol in page['AttachedPolicies']:
                arn = pol['PolicyArn']
                logger.debug(f'Detaching {arn} from {role_name}')
                self.client.detach_role_policy(PolicyArn=arn, RoleName=role_name)
                if 'aws:policy/service-role/' in arn:
                    continue # Do nothing with a service role policies
                for version in self.client.list_policy_versions(PolicyArn=arn)['Versions']:
                    if not version['IsDefaultVersion']:
                        self.client.delete_policy_version(PolicyArn=arn, VersionId=version['VersionId'])
                logger.debug(f'Deleting {arn}')
                try:
                    self.client.delete_policy(PolicyArn=arn)
                except self.client.exceptions.DeleteConflictException:
                    logger.debug(f'Policy {arn} is still used. Skipping')

        logger.debug(f'Deleting role {role_name!r}')
        try:
            self.client.delete_role(RoleName=role_name)
        except self.client.exceptions.DeleteConflictException:
            logger.debug(f'Role  {role_name!r} is still used. Skipping')

    def create_role(self, role_name: str, assume_role_policy_document: str) -> str:
        """Create IAM role with a specified name and role policy document for assuming the role"""
        response = self.client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_document, Tags=self.default_tag_list)
        return response["Role"]["Arn"]

    def get_role_arn(self, role_name: str) -> str:
        """Get the role's ARN based on the role's name"""
        response = self.client.get_role(RoleName=role_name)
        return response["Role"]["Arn"]

    def attach_policy(self, role_name: str, policy_arn: str) -> None:
        """Attach an IAM policy to an IAM role"""
        self.client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

    def create_policy_from_json(self, policy_name: str, policy_document: str) -> str:
        """Create an IAM policy from a json document and returns its ARN"""
        response = self.client.create_policy(PolicyName=policy_name, PolicyDocument=policy_document, Tags=self.default_tag_list)

        return response["Policy"]["Arn"]


def merge_policy_docs_on_resource_level(old_doc, new_doc):
    """ Returs a merged doc with statement from 2 IAM policy documents.

    This will not delete any statement, just add combining resources in statements with the same Sid. 
    Resources without Sid will be just added.
    """
    res_doc = dict(old_doc)
    for new_statement in new_doc['Statement']:
        for res_statement in res_doc['Statement']:
            if new_statement.get('Sid') and new_statement.get('Sid') == res_statement.get('Sid'):
                assert res_statement['Effect'] == new_statement['Effect'], f"Different Effects are not supported {res_statement} vs {new_statement}."
                assert sorted(res_statement['Action']) == sorted(new_statement['Action']), f"Different Actions are not supported {res_statement} vs {new_statement}."
                res_statement_res = res_statement['Resource']
                new_statement_res = new_statement['Resource']
                if isinstance(res_statement_res, str): res_statement_res = [res_statement_res]
                if isinstance(new_statement_res, str): new_statement_res = [new_statement_res]
                merged_res = sorted(list(set(res_statement_res + new_statement_res)))
                if len(merged_res) == 1: merged_res = merged_res[0]
                res_statement['Resource'] = merged_res
                break
        else:
            res_doc['Statement'].append(new_statement)
    return res_doc

def test_merge_policy_docs_on_resource_level():
    doc1 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Sid1",
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "arn:aws:s3:::*"
            },
            {
                "Sid": "Sid2",
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": [
                    "arn:aws:s3:::bucket_name1",
                    "arn:aws:s3:::bucket_name2"
                ]
            }
        ]
    }
    doc2 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Sid1",
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "arn:aws:s3:::*"
            },
            {
                "Sid": "Sid2",
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": [
                    "arn:aws:s3:::bucket_name3"
                ]
            },
            {
                "Sid": "Sid3",
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": [
                    "arn:aws:s3:::bucket_name4"
                ]
            }
        ]
    }
    res = merge_policy_docs_on_resource_level(doc1, doc2)
    assert 'arn:aws:s3:::bucket_name1' in res['Statement'][1]['Resource'], "Merge must contain resources"
    assert 'arn:aws:s3:::bucket_name2' in res['Statement'][1]['Resource'], "Merge must contain resources"
    assert 'arn:aws:s3:::bucket_name3' in res['Statement'][1]['Resource'], "Merge must contain resources"
    assert "arn:aws:s3:::*" == res['Statement'][0]['Resource'], "Merge same resources must be identical to the source"
    assert ["arn:aws:s3:::bucket_name4"] == res['Statement'][2]['Resource'], "New items must be added"


def integration_test_create_delete_role():
    iam = IAM(boto3.session.Session())
    role_name = 'test_role'
    role = iam.ensure_data_source_role_exists(role_name, buckets=['test'])
    assert role

    attached_policies = { p['PolicyName']:p['PolicyArn']
        # We cannot have more than 10 policy attached to a role. No need in paginator.
        for p in iam.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    }
    assert 'AWSQuicksightAthenaAccess' in attached_policies

    for i in range(6):
        role = iam.ensure_data_source_role_exists(role_name, buckets=[f'test{i}'])
    assert role
    iam.ensure_role_does_not_exist(role_name)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    test_create_delete()