
import learning_interface

class MatrixFactorization(learning_interface.LearningInterface):

    def __init__(self):
        super(MatrixFactorization, self).__init__()

    def extract_data(self):
        return "Extract data"

    def split_data(self):
        return "Split data"

    def train(self):
        return "Train data"
    
    def validate(self):
        return "Validate data"

    def test(self):
        return "Test data"

    def predict(self):
        return "Predict data"