from django.db import models as db_models
from main_app import models as main_app_models

from main_app.utils import utils_general
from main_app.utils import utils_date

param_extraction = utils_general.strip_string_or_none


def _extract_params(post_request):
    output = {}

    output['title'] = param_extraction(post_request.get('filter_title'))
    output['author_full_name'] = param_extraction(post_request.get('filter_author_full_name'))
    output['category'] = param_extraction(post_request.get('filter_category'))
    output['from_date'] = param_extraction(post_request.get('filter_from_date'))
    output['from_date'] = utils_date.string_to_date(output['from_date'])

    output['to_date'] = param_extraction(post_request.get('filter_to_date'))
    output['to_date'] = utils_date.string_to_date(output['to_date'])

    output['sort_by_1'] = param_extraction(post_request.get('sort_by_1'))
    output['sort_by_2'] = param_extraction(post_request.get('sort_by_2'))

    return output

def _generic_filter_paper(post_request, filter_args, filter_kwargs, order_by_fields, prepend_name):
    SORT_FIELDS = {
        'sort_by_date' : '-%screated_date' % prepend_name,
        'sort_by_title' : '%stitle' % prepend_name
    }

    extracted_params = _extract_params(post_request)
    sorting_fields = [extracted_params['sort_by_1'], extracted_params['sort_by_2']]

    if extracted_params['title']:
        filter_kwargs['%stitle__icontains' % prepend_name] = extracted_params['title']

    if extracted_params['author_full_name']:
        filter_kwargs['%sauthors__full_name__icontains' % prepend_name] = extracted_params['author_full_name']

    if extracted_params['category']:
        filter_args.append(db_models.Q(**{'%scategories__name__icontains' % prepend_name : extracted_params['category']}) \
                        | db_models.Q(**{'%scategories__code__icontains' % prepend_name : extracted_params['category']}))

    if extracted_params['from_date']:
        filter_kwargs['%screated_date__gte' % prepend_name] = extracted_params['from_date']

    if extracted_params['to_date']:
        filter_kwargs['%screated_date__lte' % prepend_name] = extracted_params['to_date']

    if [field for field in sorting_fields if field]:
        del order_by_fields[:]

    for sorting_field in sorting_fields:
        if sorting_field in SORT_FIELDS:
            order_by_fields.append(SORT_FIELDS[sorting_field])

    return {k: v for k, v in extracted_params.iteritems() if v}

def filter_paper_history(post_request, filter_args, filter_kwargs, order_by_fields):
    return _generic_filter_paper(post_request, filter_args, filter_kwargs, order_by_fields, 'paper__')


def filter_paper(post_request, filter_args, filter_kwargs, order_by_fields):
    return _generic_filter_paper(post_request, filter_args, filter_kwargs, order_by_fields, '')
