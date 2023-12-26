''' IAM helper
'''
import json
import copy
import time
import logging

from cid.base import CidBase

import boto3

logger = logging.getLogger(__name__)


class IAM(CidBase):
    """ IAM helper

    Approximate list of permissions needed for creation of IAM roles and policies:
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
    """

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('iam')

    def ensure_role_for_crawler(self, s3bucket, database, table, role_name: str='CidCmdCrawlerRole', policy_name: str="CidCmdGlueCrawlerPolicy") -> None:
        """Ensure Role for Crawler exists"""

        return self.ensure_role_with_policy(
            role_name=role_name,
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "glue.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            permissions_policies={
                policy_name: {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowListBucket",
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket"],
                            "Resource": [f"arn:aws:s3:::{s3bucket}"]
                        },
                        {
                            "Sid": "AllowReadFromBucket",
                            "Effect": "Allow",
                            "Action": [ "s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{s3bucket}/*"]
                        },
                        {
                            "Sid": "AllowGlueActions",
                            "Effect": "Allow",
                            "Action": [
                                "glue:GetDatabase",
                                "glue:GetDatabases",
                                "glue:CreateTable",
                                "glue:GetTable",
                                "glue:GetTables",
                                "glue:UpdateTable",
                                "glue:GetTableVersion",
                                "glue:GetTableVersions",
                                "glue:DeleteTableVersion",
                                "glue:CreatePartition",
                                "glue:BatchCreatePartition",
                                "glue:GetPartition",
                                "glue:GetPartitions",
                                "glue:BatchGetPartition",
                                "glue:UpdatePartition",
                                "glue:DeletePartition",
                            ],
                            "Resource": [
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:catalog",
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:database/{database}",
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:table/{database}/{table}",
                            ]
                        },
                        {
                            "Sid": "AllowWriteLogs",
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:CreateLogGroup",
                            ],
                            "Resource": [f"arn:{self.partition}:logs:*:*:/aws-glue/*"]
                        },
                    ]
                }
            },
            policy_merge_mode='MERGE_RESOURCES',
        )
    def ensure_data_source_role_exists(self, role_name, database, workgroup, buckets=[]):
        ''' Create or update a role specifically for a QS Datasource
        '''
        return self.ensure_role_with_policy(
            role_name=role_name,
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "quicksight.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            managed_policies=[ 'arn:aws:iam::aws:policy/service-role/AWSQuicksightAthenaAccess'],
            permissions_policies={
                'CidQuicksightBucketAccess': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowListBucket",
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket"],
                            "Resource": [f"arn:aws:s3:::{bucket}" for bucket in buckets]
                        },
                        {
                            "Sid": "AllowReadFromBucket",
                            "Effect": "Allow",
                            "Action": [ "s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*" for bucket in buckets]
                        },
                        {
                            "Sid": "AllowAthenaReads",
                            "Effect": "Allow",
                            "Action": [
                                "lakeformation:GetDataAccess",
                                "athena:ListDataCatalogs",
                                "athena:ListDatabases",
                                "athena:ListTableMetadata",
                            ],
                            "Resource": "*",  # required https://docs.aws.amazon.com/lake-formation/latest/dg/access-control-underlying-data.html
                                              # Cannot restrict this. See https://docs.aws.amazon.com/athena/latest/ug/datacatalogs-example-policies.html#datacatalog-policy-listing-data-catalogs
                        },
                        {
                            "Sid": "AllowGlue",
                            "Effect": "Allow",
                            "Action": [
                                "glue:GetPartition",
                                "glue:GetPartitions",
                                "glue:GetDatabases",
                                "glue:GetTable",
                                "glue:GetTables",
                            ],
                            "Resource": [
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:catalog",
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:database/{database}",
                                f"arn:{self.partition}:glue:{self.region}:{self.account_id}:table/{database}/*",
                            ],
                        },
                        {
                            "Sid": "AllowAthena",
                            "Effect": "Allow",
                            "Action": [
                                "athena:ListDatabases",
                                "athena:ListDataCatalogs",
                                "athena:ListDatabases",
                                "athena:GetQueryExecution",
                                "athena:GetQueryResults",
                                "athena:StartQueryExecution",
                                "athena:GetQueryResultsStream",
                                "athena:GetTableMetadata",
                            ],
                            "Resource": [
                                f"arn:{self.partition}:athena:{self.region}:{self.account_id}:database/{database}",
                                f"arn:{self.partition}:athena:{self.region}:{self.account_id}:workgroup/{workgroup}",
                            ]
                        }
                    ]
                }
            },
            policy_merge_mode='MERGE_RESOURCES',
        )

    def ensure_role_with_policy(self, role_name, assume_role_policy_document, permissions_policies, managed_policies, policy_merge_mode='MERGE_RESOURCES') -> None:
        """Ensure Role with Policy Exists

        mode: MERGE_RESOURCES|OVERRIDE
        permissions_policies:  a dict with name of attached policy and document as a value (None for managed policies)
        """
        # Create or update role
        try:
            self.client.get_role(RoleName=role_name)
            logger.info(f'Role {role_name} exists')
            self.client.update_assume_role_policy(RoleName=role_name, PolicyDocument=json.dumps(assume_role_policy_document))
            logger.info(f'Role {role_name} updated')
        except self.client.exceptions.NoSuchEntityException:
            self.client.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy_document))
            logger.info(f'Role {role_name} created')
            time.sleep(5) # Some times the role cannot be assumed without this delay after creation

        # Create or update policies and attach them to the role
        for policy_name, new_policy_document in permissions_policies.items():
            try:
                policy_arn = f"arn:{self.partition}:iam::{self.account_id}:policy/{policy_name}"
                policy_response = self.client.get_policy(PolicyArn=policy_arn)
                logger.info(f"Policy '{policy_name}' already exists.")

                # If the policy exists, it probably requires an update
                if isinstance(new_policy_document, dict):
                    policy_versions = self.client.list_policy_versions(PolicyArn=policy_arn)['Versions']
                    if len(policy_versions) >= 5: #policy cannot contain more than 5 versions, so we need to delete
                        for version in policy_versions[4:]:
                            self.client.delete_policy_version(PolicyArn=policy_arn, VersionId=version['VersionId'])
                            logger.info(f"Deleted policy version {version['VersionId']}.")
                    version = policy_response['Policy']['DefaultVersionId']
                    current_policy_document = self.client.get_policy_version(PolicyArn=policy_arn, VersionId=version)['PolicyVersion']['Document']

                    if policy_merge_mode == "MERGE_RESOURCES":
                        result_document = merge_policy_docs_on_resource_level(current_policy_document, new_policy_document)
                    else:
                        result_document = new_policy_document

                    logger.debug('current_policy_document=' + json.dumps(current_policy_document))
                    logger.debug('new_policy_document=' + json.dumps(new_policy_document))
                    logger.debug('result_document=' + json.dumps(result_document))
                    if result_document == current_policy_document:
                        logger.info(f"No need to update '{policy_name}' the doc is the same as requested.")
                    else:
                        logger.debug(f'Updating policy {policy_arn} to {result_document}')
                        # A managed policy can have up to 5 versions.
                        # Before you create a new version, you must delete at least one existing version.
                        versions = self.client.list_policy_versions(PolicyArn=policy_arn)['Versions']
                        if len(versions) >= 5:
                            for version in versions[::-1]:
                                if not version['IsDefaultVersion']:
                                    continue
                                self.client.delete_policy_version(PolicyArn=policy_arn, VersionId=version['VersionId'])
                                break
                        self.client.create_policy_version(PolicyArn=policy_arn, PolicyDocument=json.dumps(result_document), SetAsDefault=True)
                        logger.info(f"Policy '{policy_name}' updated.")
            except self.client.exceptions.NoSuchEntityException:
                policy_response = self.client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(new_policy_document)
                )
                logger.info(f"Policy '{policy_name}' created successfully.")

            # Attach if needed
            attached_policies = self.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
            if not any(policy['PolicyArn'] == policy_arn for policy in attached_policies):
                self.client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                logger.info(f"IAM Policy '{policy_name}' attached to the role.")

        attached_policies = self.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        for managed_policy_arn in managed_policies:
            if not any(policy['PolicyArn'] == managed_policy_arn for policy in attached_policies):
                self.client.attach_role_policy(RoleName=role_name, PolicyArn=managed_policy_arn)
                logger.info(f"Managed Policy '{managed_policy_arn}' attached to the role.")

        return role_name


    def iterate_role_names(self, search='Roles[].RoleName'):
        """ iterate role names
        """
        try:
            yield from self.client.get_paginator('list_roles').paginate().search(search)
        except self.client.exceptions.ClientError as exc:
            logger.warning('Failed to read available IEM roles: {exc}. Most likely not fatal.')




def merge_policy_docs_on_resource_level(old_doc, new_doc):
    """ Returns a merged doc with statement from 2 IAM policy documents.

    This will not delete any statement, just add combining resources in statements with the same Sid.
    Resources without Sid will be just added.
    """
    res_doc = copy.deepcopy(old_doc)
    for new_statement in new_doc['Statement']:
        for res_statement in res_doc['Statement']:
            if new_statement.get('Sid') and new_statement.get('Sid') == res_statement.get('Sid'):
                assert res_statement['Effect'] == new_statement['Effect'], f"Different Effects are not supported {res_statement} vs {new_statement}."
                assert sorted(res_statement['Action']) == sorted(new_statement['Action']), f"Different Actions are not supported {res_statement} vs {new_statement}."
                res_statement_res = res_statement['Resource']
                new_statement_res = new_statement['Resource']
                if isinstance(res_statement_res, str):
                    res_statement_res = [res_statement_res]
                if isinstance(new_statement_res, str):
                    new_statement_res = [new_statement_res]
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