import traceback
import sys

import config
from matrix_factorization import matrix_factorization

"""
request = {
    'action' : 'method name',
    'args' : ['param1', 'param2', '...'],
    'kwargs' : {
        'name' : 'value'
    }
}
"""
this_module = sys.modules[__name__]
matrix_factorization_object = None

def _return_message(status, message):
    return {
        'success' : status,
        'message' : message
    }

_return_success = lambda message : _return_message(True, message)
_return_failure = lambda message : _return_message(False, message)

def _get_learning_module():
    reload(config)
    assert hasattr(this_module, str(config.learning_module) + '_object')
    return getattr(this_module, str(config.learning_module) + '_object')

def initialize():
    global matrix_factorization_object

    matrix_factorization_object = matrix_factorization.MatrixFactorization()

def process(request):
    print 'Serving request {0}'.format(request)
    learning_module = _get_learning_module()

    if 'action' not in request:
        return _return_failure('Has to specify an action')

    args = [] if 'args' not in request else request['args']
    kwargs = {} if 'kwargs' not in request else request['kwargs']
    action = request['action']

    if not hasattr(learning_module, action):
        return _return_failure('Action not found {0}'.format(action))

    try:
        calling = getattr(learning_module, action)
        
        result, message = calling(*args, **kwargs)
        if not result:
            return _return_failure('Action execution failed.\n' + str(message))
        else:
            return _return_success(message)
    except:
        trace = traceback.format_exc()
        print trace
        return _return_failure(trace)

