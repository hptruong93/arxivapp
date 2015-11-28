from django.db import models as db_models
from main_app import models as main_app_models

from main_app.utils import utils_general
from main_app.utils import utils_date

param_extraction = utils_general.strip_string_or_none
EXTRACTING_FORM_FIELDS = ['filter_title', 'filter_author_full_name', 'filter_category', 'filter_from_date', 'filter_to_date']
EXTRACTING_FILTER_FIELDS = ['title', 'author_full_name', 'category', 'from_date', 'to_date', 'sort_by_1', 'sort_by_2']

def _extract_params(post_request):
    output = {}

    for field in EXTRACTING_FILTER_FIELDS:
        output[field] = param_extraction(post_request.get(field))

    output['from_date'] = utils_date.string_to_date(output['from_date'])
    output['to_date'] = utils_date.string_to_date(output['to_date'])

    output['make_default'] = param_extraction(post_request.get('make_default'))

    return output

def _generic_filter_paper(user, post_request, filter_args, filter_kwargs, order_by_fields, prepend_name):
    SORT_FIELDS = {
        'sort_by_date' : '-%screated_date' % prepend_name,
        'sort_by_title' : '%stitle' % prepend_name
    }

    extracted_params = _extract_params(post_request)

    sorting_fields = [extracted_params['sort_by_1'], extracted_params['sort_by_2']]

    if extracted_params['title']:
        filter_kwargs['%stitle__icontains' % prepend_name] = extracted_params['title']

    if extracted_params['author_full_name']:
        split = [s for s in extracted_params['author_full_name'].split(' ') if s]
        if len(split) == 1:
            filter_kwargs['%sauthors__full_name__icontains' % prepend_name] = extracted_params['author_full_name']
        elif len(split) > 1:
            filter_kwargs['%sauthors__first_name__icontains' % prepend_name] = ' '.join(split[:-1])
            filter_kwargs['%sauthors__last_name__icontains' % prepend_name] = split[-1]

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

    if extracted_params['make_default']:
        filter_params = {k:v for k, v in extracted_params.iteritems() if k != 'make_default'}
        filter_params['user'] = user

        new_filter, created = main_app_models.UserFilterSort.objects.get_or_create(**filter_params)

        if created:
            new_filter.user = user
        new_filter.is_default = True
        new_filter.save()

    return {k: v for k, v in extracted_params.iteritems() if v}

def filter_paper_history(request, filter_args, filter_kwargs, order_by_fields):
    post_dictionary = { (k[len('filter_'):] if k.startswith('filter_') else k) : v for k, v in request.POST.iteritems() }
    return _generic_filter_paper(request.user, post_dictionary, filter_args, filter_kwargs, order_by_fields, 'paper__')

def filter_paper(request, filter_args, filter_kwargs, order_by_fields):
    post_dictionary = { (k[len('filter_'):] if k.startswith('filter_') else k) : v for k, v in request.POST.iteritems() }
    return _generic_filter_paper(request.user, post_dictionary, filter_args, filter_kwargs, order_by_fields, '')

def filter_paper_default(request, filter_args, filter_kwargs, order_by_fields):
    try:
        default_filter = main_app_models.UserFilterSort.objects.get(user = request.user, is_default = True)
        default_filter_dict = { field : getattr(default_filter, field) for field in EXTRACTING_FILTER_FIELDS }

        if default_filter_dict.get('from_date'):
            default_filter_dict['from_date'] = utils_date.date_to_string(default_filter_dict['from_date'])

        if default_filter_dict.get('to_date'):
            default_filter_dict['to_date'] = utils_date.date_to_string(default_filter_dict['to_date'])            

        returning = _generic_filter_paper(request.user, default_filter_dict, filter_args, filter_kwargs, order_by_fields, '')
        return returning
    except main_app_models.UserFilterSort.DoesNotExist:
        return {}
