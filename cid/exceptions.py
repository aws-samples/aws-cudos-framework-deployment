
class CidError(Exception):
    """Base class for CID Exceptions"""
    pass

class CidCritical(BaseException):
    """Critical Exception, not to be catched with standard Exception"""
    pass
