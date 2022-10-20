from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(*args, **kwargs):
        ...
