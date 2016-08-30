
server_name = 'localhost'
port = 8001

learning_module = 'matrix_factorization'

CATEGORY_COUNT = 168
LDA_TOPIC_COUNT = 250 # Before modifying this number, check out lda.py for topic count.

 # A reasonable size for one batch of lda processing. If too big will take very long. If too small will waste time setting up.
LDA_CHUNK_SIZE = 1000