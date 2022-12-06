import logging

from boto3.session import Session
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

class CidBase():
    """
    Core class for cid.
    """

    _session: Session = None
    _awsIdentity: dict = None


    def __init__(self, session: Session) -> None:
        self.session = session

    @property
    def account_id(self) -> str:
        return self.awsIdentity.get('Account')

    @property
    def awsIdentity(self) -> dict:
        if not self._awsIdentity:
            try:
                sts = self.session.client('sts')
                self.awsIdentity = sts.get_caller_identity()
            except Exception as e:
                raise CidCritical(f'Authentication error: {e}')
        return self._awsIdentity

    @awsIdentity.setter
    def awsIdentity(self, value):
        self._awsIdentity = value

    @property
    def region(self) -> str:
        return self.session.region_name

    @property
    def region_name(self) -> str:
        return self.session.region_name

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def username(self) -> str:
        if not hasattr(self, "_user") or self._user is None:
            # Guess the username from identity ARN
            arn = self.awsIdentity.get('Arn')
            if arn.split(':')[5] == 'root':
                return self.account_id
            else:
                return '/'.join(arn.split('/')[1:])
        return self._user.get('UserName')
