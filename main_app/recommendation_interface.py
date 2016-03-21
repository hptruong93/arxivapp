import requests
import json
import os
import imp
import random
import datetime

config = imp.load_source('config', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'learning_framework', 'config.py'))
from main_app import models

url = 'http://{0}:{1}'.format(config.server_name, config.port)
headers = {'Content-type': 'application/json'}

ARXIV_STRATEGY = 'arxiv'
GMF_STRATEGY = 'gmf'

def _get_sort_strategy(user_id):
    """
        We randomize strategy based on user_id and date
        None means the sorting facility is not available
    """
    random.seed(str(user_id) + str(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))

    if bool(random.getrandbits(1)):
        return ARXIV_STRATEGY
    else:
        learning_module = _query_result({
            'action': 'get_learning_module'
            })

        if learning_module is not None:
            return GMF_STRATEGY
        else:
            return None

def _query_result(data):
    try:
        result = requests.post(url, headers = headers, data = json.dumps(data))
    except:
        return None

    if result.status_code != 200:
        return None

    response = result.json()
    if not response['success']:
        print "Encountered exception from server\n{0}".format(response['message'])
        return None

    return response['message']

def sort(user, papers):
    """
        Return a tuple of (sort strategy, iterable of sorted_items)
        If sort strategy is None, the input list is left untouched (i.e. no sorting involved)
    """

    data = {
        'action': 'sort',
        'args': [user.id, [paper.arxiv_id for paper in papers]]
    }
    sort_strategy = _get_sort_strategy(user.id)

    if sort_strategy == ARXIV_STRATEGY:
        return sort_strategy, sorted(papers, key = lambda p : p.arxiv_id)
    elif sort_strategy == GMF_STRATEGY:
        result = _query_result(data)
        if result is None:
            return None, papers
        else:
            output = []
            sorted_papers = result['sorted']
            uknown_papers = result['unknown']

            #Sort papers according to the recommended order.
            #Notice: Keep the order of the unknown papers the same
            output_index, unknown_index = 0, 0
            for index in sorted_papers:
                while unknown_index < len(uknown_papers):
                    if result['unknown'][unknown_index] == output_index:
                        output.append(papers[unknown_index])

                        output_index += 1
                        unknown_index += 1
                    else:
                        break

                output.append(papers[index])
                output_index += 1


            return sort_strategy, output
    else:
        return None, papers

def index(user):
    """
        Return list of recommmended papers on the index page
    """
    data = {
        'action' : 'predict',
        'args': [user.id]
    }

    result = _query_result(data)
    if result is None:
        return models.Paper.objects.filter(arxiv_id__in = ())

    try:
        ids = result['ids']
        assert type(ids) is list

        query_output = models.Paper.objects.filter(arxiv_id__in = ids) #E.g. ['1602.03276', '1602.03275']
        query_output = list(query_output)
        query_output.sort(key = lambda x : ids.index(x.arxiv_id))
        return query_output
    except:
        return models.Paper.objects.filter(arxiv_id__in = ())
    

def author(user, author_id, *args, **kwargs):
    """
        Return list of recommmended papers on the author page
    """
    return models.Paper.objects.filter(arxiv_id__in = ())

def category(user, category_code, *args, **kwargs):
    """
        Return list of recommmended papers on the category page
    """
    return models.Paper.objects.filter(arxiv_id__in = ())

def search(user, value, *args, **kwargs):
    """
        Return list of recommmended papers on the search page
    """
    return models.Paper.objects.filter(arxiv_id__in = ())