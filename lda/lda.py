
import uuid
import subprocess
import shutil
import sys
import os
import re
import collections

import numpy as np

_TEMP_DIR = lambda : "/tmp/lda_temp_{0}".format(uuid.uuid4().hex)
_GSL_LIB_PATH = "/home/ml/arxivapp/site/arxivapp/lda/gsl/gsl_installed/lib"
_LDA_BINARY = "/home/ml/arxivapp/site/arxivapp/lda/lda_topics/lda"
_VOCABULARY_PATH = "/home/ml/arxivapp/site/arxivapp/lda/lda_topics/vocab.dat"

_DATA_FILE = 'data.dat' # Relative to temp dir
_OUTPUT_MATRIX_FILE = 'ldafit-test.topics' # Relative to temp dir

_TOPIC_COUNT = 250

MAX_PROCESSING_LENGTH = sys.maxint

vocabulary_list = None
vocabulary_dict = None

def _create_divisor(x):
    """
        Return 1 if input is zero, else return the input.
    """
    return x if x != 0 else 1

def _get_word_list(text):
    """
        Return a list of words in this string.
    """
    return re.findall('\w+', text)

def load_vocabulary():
    """
        Load the list of known vocabulary from the default vocabulary file.
        This also loads the reverse dictionary mapping from vocabulary to index.
    """
    global vocabulary_list, vocabulary_dict
    vocabulary_list = []
    vocabulary_dict = {}

    with open(_VOCABULARY_PATH, 'r') as f:
        for index, line in enumerate(f):
            line = line.strip()
            vocabulary_dict[line] = index
            vocabulary_list.append(line)

def _word_count(word_list):
    return collections.Counter([word for word in word_list if word in vocabulary_dict])

def _word_counter_to_matrix_text(word_counter):
    output = [(vocabulary_dict[word], count) for word, count in word_counter.items()]

    # output = sorted(output) # Optional sorting
    output = map(lambda x : '{0}:{1}'.format(x[0], x[1]), output)

    return '{0} {1}'.format(len(output), ' '.join(output)) if len(output) > 0 else ''

def _word_counter_to_matrix_row(word_counter):
    """
        Convert a word counter to a single row whose length is len(vocabulary_list) and value at each index is the frequency.
    """
    output = np.zeros(len(vocabulary_list), dtype = int)
    for word, count in word_counter.items():
        assert word in vocabulary_dict
        output[vocabulary_dict[word]] = count

    return output


def _to_data_file(converted_papers):
    """
        Write the data to the data file.
        Create temp directory if need be, or clean existing temp directory.
        Input is a list of strings in the following format:
            n w1:c1 w2:c2 ...
            where n is the total amount of distinct terms encountered (w1, w2, ..., wn)
            w1, w2, w3, ..., wn are the distinct terms encountered
            c1, c2, c3, ..., cn are the frequencies of occurrences of the according terms w1, w2, w3, ...

        return the temporary directory where the file is written into
    """

    temp_dir = _TEMP_DIR()
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    else: # Clean dir
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

    with open(os.path.join(temp_dir, _DATA_FILE), 'w') as f:
        for converted_paper in converted_papers:
            if not converted_paper:
                continue
            f.write(converted_paper)
            f.write('\n')

    return temp_dir

def _lda(temp_dir, data_file = _DATA_FILE):
    # Get absolute paths
    data_file = os.path.join(temp_dir, data_file)
    output_matrix_file = os.path.join(temp_dir, _OUTPUT_MATRIX_FILE)

    cmd = './lda --test_data {0} --num_topics {1} --directory {2} --model_prefix ldafit'.format(data_file, _TOPIC_COUNT, temp_dir)
    print '${0}'.format(cmd)
    environment = os.environ.copy()
    environment['LD_LIBRARY_PATH'] = _GSL_LIB_PATH
    subprocess.check_call(cmd, shell = True, cwd = os.path.dirname(_LDA_BINARY), env = environment)

    return np.loadtxt(output_matrix_file, dtype = int)

def _grade(lda_result, word_counters):
    """
        Grade for each topic is the sum of product of word count and the weight of that word in the loaded lda result.
        Grade is also normalized by paper (by considering all topics for that paper).
        return a matrix whose rows are the counters representing the papers and columns are topic.
    """
    row_list = map(_word_counter_to_matrix_row, word_counters)
    matrix = np.array(row_list, dtype = int) # paper x words

    output = np.dot(lda_result, matrix.T) # (topics x words) x (words x paper) --> topics x paper

    # Now perform normalization.
    # Note that here we utilize the default behavior of sum in numpy does summing by column, which is summing by paper as we want.
    # In addition, divide also perform operations row by row, which is also what we want.
    divisor_creator = np.vectorize(_create_divisor) # This is to avoid dividing by zero
    output = np.true_divide(output, divisor_creator(sum(output))) # Dividing each column by its sum to normalize

    return output.T

def extract_lda(papers, clean_up = True):
    """
        Extract lda for a list of papers. This is a list of papers whose attributes "abstract" will be parsed for words.
        return a matrix whose rows are the paper with the same index, and columns are the topics. This matrix is normalized by row.
    """
    assert len(papers) <= MAX_PROCESSING_LENGTH
    paper_abstracts = [_get_word_list(paper.abstract) for paper in papers]

    data = map(_word_count, paper_abstracts)
    temp_dir = _to_data_file(map(_word_counter_to_matrix_text, data))
    lda_result = _lda(temp_dir)

    if clean_up:
        shutil.rmtree(temp_dir)

    return _grade(lda_result, data)


if __name__ == "__main__":
    # Sample usage
    load_vocabulary()

    class Test: # Dummy class
        pass

    test_object = Test()
    test_object.abstract = 'a new study has shown that energy field from time function alters system state'

    test_object1 = Test()
    test_object1.abstract = 'another new study has shown that energy field from time function alters system state'

    result = extract_lda([test_object, test_object1])
    print result
    print result.shape