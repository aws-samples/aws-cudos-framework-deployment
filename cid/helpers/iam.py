# flake8: noqa: E501
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class RoleExistsException(Exception):
    ...


class IAM(CidBase):
    """ IAM helper class"""
    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('iam', region_name=self.region)

    def create_role(self, role_name: str, assume_role_policy_document: str) -> str:
        try:
            response = self.client.create_role(RoleName=role_name, 
                                            AssumeRolePolicyDocument=assume_role_policy_document)
            return response['Role']['Arn']
        except self.client.exceptions.EntityAlreadyExistsException:
            raise RoleExistsException(f'{role_name} already exists')

    def get_role_arn(self, role_name: str) -> str:
        response = self.client.get_role(RoleName=role_name)
        return response['Role']['Arn']
    
    def attach_policy(self, role_name: str, policy_arn: str) -> None:
        response = self.client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    
    def create_policy_from_json(self, policy_name: str, policy_document: str) -> str:
        """ Creates an IAM policy from a json document and returns its ARN"""
        response = self.client.create_policy(PolicyName=policy_name, PolicyDocument=policy_document)

        return response['Policy']['Arn']
    