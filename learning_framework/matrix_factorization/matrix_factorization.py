import datetime
import random
import os
import sys
print os.path.abspath('..')
sys.path.insert(0, os.path.abspath('..'))

#Setting up environment variable for django to work
os.environ['DJANGO_SETTINGS_MODULE'] = 'arxivapp.settings'
from main_app import models
from django.contrib.auth import models as auth_models
from django.db.models import Q

import numpy as np

import gmf
import learning_interface

DATA_ROOT = '/home/ml/arxivapp/site/arxivapp/test_data'
#Start year
YEAR = 2014

#Global variables
category_map = {} #Map from category code -> index (0-n)
category_reversed_map = {} #Map from index (0-n) -> category_code
index_paper_map = {} #Map from paper_id -> index (0-n)
index_paper_reversed_map = {} #Map from index --> paper_id
index_user_map = {} #Map from user_id -> index (0-n)
train_points = {}
v_matrix = {}

def interested_year():
    return datetime.datetime(year = datetime.datetime.now().year - 1, month = 1, day = 1)

def get_interested_papers():
    return models.Paper.objects.filter(created_date__gte = datetime.datetime(year = YEAR, month = 1, day = 1)).order_by('arxiv_id')

def write_dict(dictionary, file_name, inversed = True):
    with open(file_name, 'w') as f:
        for key, value in dictionary.iteritems():
            if not inversed:
                f.write('{0} {1}'.format(key, value))
            else:
                f.write('{0} {1}'.format(value, key))
            f.write('\n')

def write_double_dict(dictionary, file_name):
    with open(file_name, 'w') as f:
        for row, col_object in dictionary.iteritems():
            for col, value in col_object.iteritems():
                f.write('{0} {1} {2}'.format(row, col, value))
                f.write('\n')

def split_dict(dictionary, p_split):
    output1 = {}
    output2 = {}

    def _add_to_dict(dictionary, row, col, value):
        if row not in dictionary:
            dictionary[row] = {}
        dictionary[row][col] = value

    for row, col_object in dictionary.iteritems():
        for col, value in col_object.iteritems():
            if random.random() < p_split:
                _add_to_dict(output1, row, col, value)
            else:
                _add_to_dict(output2, row, col, value)

    return output1, output2

def map_paper_data():
    global index_paper_map, index_paper_reversed_map
    index_paper_map = {}
    index_paper_reversed_map = {}

    doing = get_interested_papers()
    print "Collecting {0} papers".format(doing.count())

    count = 0
    for paper in doing:
        index_paper_map[paper.arxiv_id] = count
        index_paper_reversed_map[count] = paper.arxiv_id
        count += 1

def map_user_data():
    global index_user_map
    index_user_map = {}

    print "Collecting user data"
    doing = auth_models.User.objects.all()
    count = 0
    for user in doing:
        index_user_map[user.id] = count
        count += 1

def map_uv():
    print "Forming UxV matrix"
    global train_points
    train_points = {}

    def _add_point(arxiv_id, user_id, point = 1):
        if arxiv_id not in index_paper_map:
            print "Something wrong?"
            return

        user_index = index_user_map[user_id]
        papper_index = index_paper_map[arxiv_id]

        if user_index not in train_points:
            train_points[user_index] = {}

        if papper_index in train_points[user_index]:
            train_points[user_index][papper_index] += point
        else:
            train_points[user_index][papper_index] = point

    paper_views = models.PaperHistory.objects.filter(last_access__gte = interested_year())
    for view in paper_views:
        _add_point(view.paper.arxiv_id, view.user_id, 1)

    paper_close_views = models.FullPaperViewHistory.objects.filter(last_access__gte = interested_year())
    for close_view in paper_close_views:
        _add_point(close_view.paper.arxiv_id, close_view.user_id, 2)        

def map_category():
    global category_map, category_reversed_map
    category_map = {}
    category_reversed_map = {}

    print "Collecting categories"
    index = 0
    for category in models.Category.objects.all():
        category_map[category.code] = index
        category_reversed_map[index] = category.code
        index += 1

def generate_v_matrix():
    print "Generating V matrix"
    """
        Generate paper x category (i.e. v_matrix)
        matrix[paper][category] = 1 if paper belongs to that category
    """
    global v_matrix
    v_matrix = {}

    for paper in get_interested_papers():
        paper_index =  index_paper_map[paper.arxiv_id]
        for category in paper.categories.all():
            category_index = category_map[category.code]

            if paper_index not in v_matrix:
                v_matrix[paper_index] = {}

            v_matrix[paper_index][category_index] = 1

def print_output():
    global train_points
    print "Printing to files"
    write_dict(index_paper_map, os.path.join(DATA_ROOT, 'paper_map.tsv'))
    write_dict(index_user_map, os.path.join(DATA_ROOT, 'user_map.tsv'))
    write_dict(category_map, os.path.join(DATA_ROOT, 'category_map.tsv'))
    write_double_dict(v_matrix, os.path.join(DATA_ROOT, 'V.tsv'))

    train_points, non_train_points = split_dict(train_points, 0.8)
    validation_points, test_points = split_dict(non_train_points, 0.5)

    write_double_dict(train_points, os.path.join(DATA_ROOT, 'train.tsv'))
    write_double_dict(validation_points, os.path.join(DATA_ROOT, 'validation.tsv'))
    write_double_dict(test_points, os.path.join(DATA_ROOT, 'test.tsv'))

##############################################################################################################################
##############################################################################################################################

class MatrixFactorization(learning_interface.LearningInterface):

    def __init__(self):
        super(MatrixFactorization, self).__init__()
        self.model = None

    def extract_data(self):
        self.model = None
        execution = [map_paper_data, map_user_data, map_category, generate_v_matrix, map_uv]
        for index, function in enumerate(execution):
            function()

        return True, "Data extracted"

    def split_data(self):
        print_output()
        with open(os.path.join(DATA_ROOT, 'U.tsv'), 'w') as f:
            f.write('0 0 0\n0 1 0\n1 0 0')

        return True, "Split data"

    def train(self, k, lambda_u, lambda_v, data_name = 'TEST', input_nneg = False, input_nitems = None, input_nusers = None, input_load_data = False):
        nusers, nitems, train, valid, test, idx0_user, idx0_item = gmf.load_data(DATA_ROOT)
        nitems = max(nitems, len(index_paper_reversed_map))
        nusers = max(nusers, len(index_user_map))

        if input_nitems:
            nitems = input_nitems

        if input_nusers:
            nusers = input_nusers

        eval_dir = '%s-nusers%d-mitems%d-k%d-lu%s-lu%s' % (data_name, nusers, nitems, k, str(lambda_u).rstrip('0'), str(lambda_v).rstrip('0'))
        if input_nneg:
            eval_dir += '-nneg'

        if not os.path.exists(eval_dir):
            os.mkdir(eval_dir)
            print '+ creating eval dir:', eval_dir
        else:
            print '+ using eval dir:', eval_dir

        b = float(train.shape[0]) / (nusers * nitems)
        print '+ b:', b

        self.model = gmf.Model(nusers, nitems, b=b, k=k, u_vprior=lambda_u, v_vprior=lambda_v, experiment_dir=eval_dir,nneg=input_nneg,idx0_user=idx0_user, idx0_item=idx0_item)
        if not input_load_data:
            errs = gmf.run(self.model, train, valid, test, nusers, nitems, 100)
        else:
            U = np.loadtxt(os.path.join(DATA_ROOT, 'U.tsv'))
            V = np.loadtxt(os.path.join(DATA_ROOT, 'V.tsv'))

            U = gmf.to_mat(U, nusers, k)[0].toarray()
            V = gmf.to_mat(V, nitems, k)[0].toarray()

            if U.shape[1] != k:
                U = U[:,-k:]
                print 'resizing U to', U.shape
            if V.shape[1] != k:
                V = V[:,-k:]
                print 'resizing V to', V.shape
            self.model.load(U,V)
            print '+ U&V loaded'
            errs = gmf.run(self.model, train, valid, test, nusers, nitems, 100, test_only=False)

        return True, "Train data"

    def retrain(self, reload_uv = True, reload_u = False, reload_v = False):
        #Update the data from database
        if reload_uv:
            map_uv()

        if reload_u:
            pass

        if reload_v:
            pass
        
        print_output()

        ############################################
        # Now retrain
        nusers, nitems, train, valid, test, idx0_user, idx0_item = gmf.load_data(DATA_ROOT)
        nitems = max(nitems, len(index_paper_reversed_map))
        nusers = max(nusers, len(index_user_map))
        gmf.run(self.model, train, valid, test, nusers, nitems, 100, test_only=False)
        return True, "Retrain data"

    def validate(self):
        return False, "Validate data"

    def test(self):
        return False, "Test data"

    def predict(self, user_id):
        print "Predicting for user_id {0}".format(user_id)

        if user_id not in index_user_map:
            message = "Cannot find user with id {0}".format(user_id)
            return False, message

        user_index = index_user_map[user_id]
        if self.model is None:
            return False, "Model is None"

        result = self.model.predict_user(user_index, max_items = 10)
        result = [index_paper_reversed_map[papper_index] for papper_index in result if papper_index in index_paper_reversed_map]

        return True, {
            'ids' : list(result)
        }

        # return {
        #     'ids' : ['1602.03276', '1602.03275']
        # }