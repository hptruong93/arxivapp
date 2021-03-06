from abc import ABCMeta
from abc import abstractmethod
import threading

class LearningInterface(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        super(LearningInterface, self).__init__()
        self._lock = threading.Lock()

    def is_locked(self):
        return self._lock.locked()

    def lock(self):
        self._lock.acquire(True) # Blocking

    def unlock(self):
        self._lock.release()

    @abstractmethod
    def extract_data(self):
        """
            Extract data from database, forming the required structure in memory.
            After this method is call, the client should not interact with the database any more
        """
        pass

    @abstractmethod
    def split_data(self):
        """
            Split the extracted data into appropriate portions used for training/validation/testing
            Prepare the data set to be ready for training step.
        """
        pass

    @abstractmethod
    def train(self):
        """
            Magic happens here
        """
        pass

    @abstractmethod
    def retrain(self):
        """
            Reload data from databse or other sources, then train again
        """
        pass

    @abstractmethod
    def validate(self):
        """
            Validate the training result (if applicable) using the validation dataset (if applicable).
        """
        pass

    @abstractmethod
    def test(self):
        """
            Test the traning result (if applicable) using the test dataset (if applicable).
        """
        pass

    @abstractmethod
    def predict(self):
        """
            Predict a range of (user, paper), or a specific paper
        """
        pass

    @abstractmethod
    def sort(self):
        """
            Sort a collection of papers in terms of descending preference1
        """
        pass