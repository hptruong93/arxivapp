from django.db import models as db_models
from main_app import models as main_app_models

from main_app.utils import utils_general
from main_app.utils import utils_date

_FILTER_PREFIX = "filter_"

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
    output['page'] = param_extraction(post_request.get('page'))
    output['page'] = int(output['page']) if output['page'] is not None else 1

    return output

def _generic_filter_paper(user, post_request, filter_args, filter_kwargs, order_by_fields, prepend_name, filter_type = None):
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
        split = []
        if ',' in extracted_params['category']:
            split = extracted_params['category'].split(',')
        else:
            split = [extracted_params['category']]

        # Enable if only allow one category
        # split = split[0:1] if len(split) > 0 else split

        _primary_code = '%sprimary_category__code__icontains' % prepend_name
        _category_code = '%scategories__code__icontains' % prepend_name
        _or_function = lambda x, y : x | y

        if filter_type == 'cross_list' and len(split) > 0:
            # We filter for papers which do NOT have primary categories in the list, but have categories in the list
            # 1st: have category in the list
            conditions = [db_models.Q(**{_category_code : category}) for category in split]
            final_condition = reduce(_or_function, conditions)
            filter_args.append(final_condition)

            # 2nd: not have primary category in the list
            conditions = [db_models.Q(**{_primary_code : category}) for category in split]
            final_condition = reduce(_or_function, conditions)
            filter_args.append(~final_condition) # Not any of the primary category

        elif filter_type == 'main' and len(split) > 0:
            # Search for main category(ies)
            conditions = [db_models.Q(**{_primary_code : category}) for category in split]

            # Now or all conditions
            final_condition = reduce(_or_function, conditions)
            filter_args.append(final_condition)

        elif len(split) > 0: # This also includes type recommendation
            # Search for category(ies)
            conditions = [db_models.Q(**{_category_code : category}) for category in split]
            # Now or all conditions
            final_condition = reduce(_or_function, conditions)
            filter_args.append(final_condition)

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
        filter_params = { k : v for k, v in extracted_params.iteritems() if k != 'make_default' and k != 'page' }
        filter_params['user'] = user

        new_filter, created = main_app_models.UserFilterSort.objects.get_or_create(**filter_params)

        if created:
            new_filter.user = user
        new_filter.is_default = True
        new_filter.save()

    extracted_params['from_date'] = utils_date.date_to_string(extracted_params['from_date'])
    extracted_params['to_date'] = utils_date.date_to_string(extracted_params['to_date'])
    return {k: v for k, v in extracted_params.iteritems() if v}

def filter_paper_history(request, filter_args, filter_kwargs, order_by_fields):
    post_dictionary = { (k[len(_FILTER_PREFIX):] if k.startswith(_FILTER_PREFIX) else k) : v for k, v in request.POST.iteritems() }
    return _generic_filter_paper(request.user, post_dictionary, filter_args, filter_kwargs, order_by_fields, 'paper__')

def filter_paper(request, filter_args, filter_kwargs, order_by_fields, filter_type):
    post_dictionary = { (k[len(_FILTER_PREFIX):] if k.startswith(_FILTER_PREFIX) else k) : v for k, v in request.POST.iteritems() }
    return _generic_filter_paper(request.user, post_dictionary, filter_args, filter_kwargs, order_by_fields, '', filter_type)

def filter_paper_default(request, filter_args, filter_kwargs, order_by_fields, filter_type):
    try:
        default_filter = main_app_models.UserFilterSort.objects.get(user = request.user, is_default = True)
        default_filter_dict = { field : getattr(default_filter, field) for field in EXTRACTING_FILTER_FIELDS }

        if default_filter_dict.get('from_date'):
            default_filter_dict['from_date'] = utils_date.date_to_string(default_filter_dict['from_date'])

        if default_filter_dict.get('to_date'):
            default_filter_dict['to_date'] = utils_date.date_to_string(default_filter_dict['to_date'])

        returning = _generic_filter_paper(request.user, default_filter_dict, filter_args, filter_kwargs, order_by_fields, '', filter_type)
        return returning
    except main_app_models.UserFilterSort.DoesNotExist:
        return {}
