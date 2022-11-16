from abc import ABC, abstractmethod


class Command(ABC):
    """ Abstract base class for commands"""
    @abstractmethod
    def __init__(self, cid, logger=None, **kwargs):
        """ Initialize the class """
        
    @abstractmethod
    def execute(self, *args, **kwargs):
        """ Run the command"""
