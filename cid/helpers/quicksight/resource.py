class CidQsResource():
    def __init__(self, raw: dict) -> None:
        self.raw: dict = raw

    @property
    def name(self) -> str:
        return self.get_property('Name')

    @property
    def arn(self) -> str:
        return self.get_property('Arn')

    @property
    def account_id(self) -> str:
        return self.arn.split(':')[4]

    def get_property(self, property: str) -> str:
        return self.raw.get(property)
