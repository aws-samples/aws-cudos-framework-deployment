''' IAM helper
'''
import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class IAM(CidBase):
    """ IAM helper
    """

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('iam')

    def ensure_role_for_crawler(self, s3bucket, database, table, role_name: str='CidCmdCrawlerRole', policy_name: str="CidCmdGlueCrawlerPolicy") -> None:
        """Ensure Role for Crawler exists"""

        return self.ensure_role_with_policy(
            role_name=role_name,
            policy_name=policy_name,
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
            permissions_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket"],
                        "Resource": [f"arn:aws:s3:::{s3bucket}"]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [ "s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{s3bucket}/*"]
                    },
                    {
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
        )

    def ensure_role_with_policy(self, role_name, assume_role_policy_document, policy_name, permissions_policy_document) -> None:
        """Ensure Role with Policy Exists"""
        try:
            self.client.get_role(RoleName=role_name)
            logger.info(f'Role {role_name} exists')

            self.client.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=json.dumps(assume_role_policy_document)
            )
            logger.info(f'Role {role_name} updated')
        except self.client.exceptions.NoSuchEntityException:
            self.client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
            )
            logger.info(f'Role {role_name} created')

        try:
            policy_response = self.client.get_policy(PolicyArn=f"arn:aws:iam::{self.account_id}:policy/{policy_name}")
            logger.info(f"Policy '{policy_name}' already exists.")

            versions_response = self.client.list_policy_versions(PolicyArn=policy_response['Policy']['Arn'])
            policy_versions = versions_response['Versions']

            if len(policy_versions) >= 5:
                for version in policy_versions[4:]:
                    self.client.delete_policy_version(PolicyArn=policy_response['Policy']['Arn'], VersionId=version['VersionId'])
                    logger.info(f"Deleted policy version {version['VersionId']}.")

            # If the policy exists, update it
            self.client.create_policy_version(
                PolicyArn=policy_response['Policy']['Arn'],
                PolicyDocument=json.dumps(permissions_policy_document),
                SetAsDefault=True
            )
            logger.info(f"Policy '{policy_name}' updated.")

        except self.client.exceptions.NoSuchEntityException:
            policy_response = self.client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy_document)
            )
            logger.info(f"Policy '{policy_name}' created successfully.")

        attached_policies = self.client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        policy_arn = policy_response['Policy']['Arn']

        if not any(policy['PolicyArn'] == policy_arn for policy in attached_policies):
            self.client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"IAM Policy '{policy_name}' attached to the role.")


    def iterate_role_names(self, search='Roles[].RoleName'):
        """ iterate role names
        """
        try:
            yield from self.client.get_paginator('list_roles').paginate().search(search)
        except self.client.exceptions.ClientError as exc:
            logger.warning('Failed to read available IEM roles: {exc}. Most likely not fatal.')
