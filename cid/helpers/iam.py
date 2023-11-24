import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class IAM(CidBase):

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('iam')

    def create_role_for_crawler(self) -> None:
        raise NotImplementedError()