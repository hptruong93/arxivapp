from abc import ABCMeta
from abc import abstractmethod

class LearningInterface(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        super(LearningInterface, self).__init__()

    @abstractmethod
    def extract_data(self):
        pass

    @abstractmethod
    def split_data(self):
        pass

    @abstractmethod
    def train(self):
        pass
    
    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def test(self):
        pass

    @abstractmethod
    def predict(self):
        pass    