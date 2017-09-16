import json
import os
import sys
import logging
import csv
import re
import time
import argparse

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cross_validation import train_test_split

import nltk
nltk.data.path.append("/NOBACKUP/ptruon4/nltk")
from nltk.corpus import stopwords

import gmf

print("Finished importing libraries.")

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s][%(lineno)d] - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

logger = logging.getLogger(__name__)
logger.info("Finished setting up logger.")

ENCODER_NOENCODER = 0
ENCODER_AUTOENCODER = 1
ENCODER_LDA = 2

N_USERS = 5551
N_PAPERS = 16981
NGRAM_RANGE = (1,3)
N_FEATURE_WORD_BAG = 40000


def process_abstract(abstract):
    letters_only = re.sub("[^a-zA-Z]", " ", abstract)
    words = letters_only.lower().split()
    stops = set(stopwords.words('english'))
    meaningful_words = [w for w in words if not w in stops]

    return ' '.join(meaningful_words)

def read_papers():
    cols = [ "doc_id", "title", "paper_id", "raw_title", "abstract" ]

    output = []
    with open('data/raw-data.csv', 'r', encoding='ISO-8859-1') as f: # Python 3
    # with open('data/raw-data.csv', 'r') as f: # Python 2
        reader = csv.reader(f, delimiter=',')
        for index, row in enumerate(reader):
            if index == 0:
                continue

            # if index == 10:
            #     break
            try:
                row[0] = int(row[0]) - 1 # zero indexed
                row[2] = int(float(row[2])) - 1 # zero indexed

                output.append([row[0], row[-1]]) # doc id and abstract
            except:
                print(row)

    return output

def read_likes(): # user x doc
    indices = []
    with open('data/user-info.csv', 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for index, row in enumerate(reader):
            if index == 0:
                continue

            # if index == 10:
            #     break

            indices.append((int(row[0]) - 1, int(row[1]) - 1))

    return indices

def load_uv(model, k, uv_loader):
    U, V = uv_loader() # uv_loader should provide two matrices.

    # uv_loader should have transformed the loaded matrices into this form, so we don't need these two lines
    # U = gmf.to_mat(U, N_USERS, k)[0].toarray()
    # V = gmf.to_mat(V, N_PAPERS, k)[0].toarray()

    # set_trace()
    if U.shape[1] != k:
      U = U[:,-k:]
      logger.info('resizing U to %s', U.shape)
    if V.shape[1] != k:
      V = V[:,-k:]
      logger.info('resizing V to %s', V.shape)
    model.load(U,V)
    logger.info('+ U&V loaded')

def main(args):
    papers = read_papers()
    for paper in papers:
        paper[1] = process_abstract(paper[1])
    logger.info("Finished preprocessing abstracts.")

    indices = read_likes()

    np.random.shuffle(indices)
    train_val, test = train_test_split(indices, test_size = 0.2)
    train, validation = train_test_split(train_val, test_size = 0.5)

    def extend_column(indices_pairs):
        array = [[pair[0], pair[1], 1] for pair in indices_pairs]
        return np.array(array, dtype = np.int32)

    train = extend_column(train)
    validation = extend_column(validation)
    test = extend_column(test)

########################################################################################################################
########################################## Raw features extraction #####################################################
########################################################################################################################
    # Construct u matrix
    with open('data/vocab.dat', 'r') as f:
        vocabulary = f.readlines()
    vocabulary = [term[:-1] for term in vocabulary]

    logger.info("Start vectorizing...")
    vectorizer = CountVectorizer(analyzer = "word",   \
                                tokenizer = None,    \
                                preprocessor = None, \
                                stop_words = None,   \
                                # vocabulary = vocabulary, \
                                ngram_range= NGRAM_RANGE, \
                                max_features = N_FEATURE_WORD_BAG)
    # fit_transform() does two functions: First, it fits the model
    # and learns the vocabulary; second, it transforms our training data
    # into feature vectors. The input to fit_transform should be a list of
    # strings.
    train_data_features = vectorizer.fit_transform([paper[1] for paper in papers])
    logger.info("Finished vectorizing. Result is {}".format(train_data_features.shape))

########################################################################################################################
############################################### Autoencoder ############################################################
########################################################################################################################

    if args.encoder == ENCODER_AUTOENCODER:
        encoding_file_path = '/NOBACKUP/ptruon4/tmp/encoded.bin'

        if args.autoencoder_load:
            train_data_features = np.load(encoding_file_path + '.npy')
        else:
            import doc_encoder
            train_data_features = doc_encoder.autoencode_paper(train_data_features.todense())
            np.save(encoding_file_path, train_data_features)
            return # Terminate the process to release GPU memory. Next time around we'll load the encoded matrix.

########################################################################################################################
#################################################### LDA ###############################################################
########################################################################################################################

    if args.encoder == ENCODER_LDA:
        import lda
        logger.info("LDA loading vocabulary...")
        lda.load_vocabulary()
        logger.info("LDA finished loading vocabulary...")

        class Dummy:
            pass

        formatted_papers = []
        for paper in papers:
            dummy_paper = Dummy()
            dummy_paper.abstract = paper[1]
            formatted_papers.append(dummy_paper)

        start_time = time.time()
        train_data_features = lda.extract_lda(formatted_papers, False)
        logger.info("LDA finished after {0}s with result {1}".format(time.time() - start_time, train_data_features.shape))

########################################################################################################################
############################################### Load V matrix ##########################################################
########################################################################################################################

    def uv_loader():
        logger.info("Loading V matrix of dimension {0}".format(train_data_features.shape))
        k = train_data_features.shape[1]

        U = np.zeros((N_USERS, k))
        V = train_data_features

        U = sparse.csr_matrix(U).toarray()
        V = sparse.csr_matrix(V).toarray()

        return U, V

########################################################################################################################
########################################################################################################################

    data_name = 'TEST'
    b = float(train.shape[0]) / (N_USERS * N_PAPERS)
    if args.encoder == ENCODER_NOENCODER:
        k = 512
    else:
        k = train_data_features.shape[1]

    lambda_u = args.u_regularizer
    lambda_v = 1

    eval_dir = '%s-nusers%d-mitems%d-k%d-lu%s-lu%s' % (data_name, N_USERS, N_PAPERS, k, str(lambda_u).rstrip('0'), str(lambda_v).rstrip('0'))
    eval_dir = '/NOBACKUP/ptruon4/tmp/' + eval_dir

    if not os.path.exists(eval_dir):
        logger.info('+ creating eval dir: %s' % os.path.abspath(eval_dir))
        os.makedirs(eval_dir)
    else:
        logger.info('+ using eval dir: %s' % eval_dir)

    model =   gmf.Model(N_USERS,
                        N_PAPERS,
                        b = b,
                        k = k,
                        u_vprior = lambda_u,
                        v_vprior = lambda_v,
                        experiment_dir = eval_dir,
                        nneg = False,
                        idx0_user = True,
                        idx0_item = True)

    if args.encoder != ENCODER_NOENCODER:
        load_uv(model, k, uv_loader)

    result = gmf.run(model, train, validation, test, N_USERS, N_PAPERS, 100)
    print(json.dumps(result, indent=4, sort_keys=True))
########################################################################################################################
########################################################################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Track files and directories for changes')
    parser.add_argument('-e', '--encoder', dest='encoder', type = int, default = ENCODER_AUTOENCODER, help='Choose encoder (autoencoder or lda).')
    parser.add_argument('-u', '--u_regularizer', dest='u_regularizer', type = float, default = 1, help='Regularizer for u.')
    parser.add_argument('-atl', '--auto-encoder-load', dest='autoencoder_load', action='store_true', default=False, help='Load autoencoder result.')
    args = parser.parse_args()
    main(args)