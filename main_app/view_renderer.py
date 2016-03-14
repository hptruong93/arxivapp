from django import shortcuts
from django.core import paginator

from main_app.history_tracking import history_tracking
from main_app.view_filters_sorts import paper_filter_sorts
from main_app import central_config as config
from main_app.utils import utils_general

from main_app import recommendation_interface

def general_filter_check(request, default_filter = False, cross_list = False):
    filter_args = []
    filter_dict = {}
    order_by_fields = ['-created_date', 'title']

    filter_data = {}
    if request.method == "POST":
        filter_data = paper_filter_sorts.filter_paper(request, filter_args, filter_dict, order_by_fields, cross_list)
    elif default_filter:
        filter_data = paper_filter_sorts.filter_paper_default(request, filter_args, filter_dict, order_by_fields, cross_list)

    return filter_args, filter_dict, order_by_fields, filter_data

def query_filter(query, filter_args, filter_dict, order_by_fields):
    output = query

    for arg in filter_args:
        if type(arg) is dict:
            output = output.filter(**arg)
        else:
            output = output.filter(arg)

    if filter_dict:
        output = output.filter(**filter_dict)

    if order_by_fields:
        output = output.order_by(*order_by_fields)

    return output

def prepare_view_articles(current_user, articles, page_number, log_paper_surf = True, tab_name = None, sort_strategy = None):
    """
        Preprocess the articles with information to put on html template
        It is important to use pagination here and leverage the lazy nature of django model
        (i.e. only those articles on the current page are fetched from db)

        Without pagination, it would be impossible to fit all papers into memory and process them.
    """
    pagination = paginator.Paginator(articles, config.MAX_ARTICLE_DISPLAY)
    displayed_page_number = page_number

    try:
        sorted_articles = pagination.page(page_number)
    except paginator.PageNotAnInteger: #Show first page
        sorted_articles = pagination.page(1)
        displayed_page_number = 1
    except paginator.EmptyPage: #Otherwise show last page if page out of range
        sorted_articles = pagination.page(pagination.num_pages)
        displayed_page_number = pagination.num_pages

    surf_group = None
    if log_paper_surf:
        surf_group = history_tracking.log_paper_surf(current_user, articles, displayed_page_number, tab_name, sort_strategy)

    for article in sorted_articles:
        article.all_authors = article.authors.all()
        article.all_categories = article.categories.all()

    return utils_general._n_group(sorted_articles, config.MAX_COLUMN_DISPLAYED), sorted_articles, surf_group

def render_papers(request, articles, cross_list = None, recommended_articles = None, sort_strategy = None, additional_data = None):
    articles, paginated_articles, surf_group = prepare_view_articles(request.user, articles, request.GET.get('page'), tab_name = 'latest', sort_strategy = sort_strategy)
    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles,
        'latest_surf_group': surf_group.id
    }

    if cross_list is not None:
        cross_list_articles, paginated_cross_list_articles, surf_group = prepare_view_articles(request.user, cross_list, request.GET.get('page'), tab_name = 'cross_list', sort_strategy = sort_strategy)
        data['cross_list_articles'] = cross_list_articles
        data['paginated_cross_list_articles'] = paginated_cross_list_articles
        data['cross_list_surf_group'] = surf_group.id

    if recommended_articles is not None:
        recommended_articles, paginated_recommended_articles, _ = prepare_view_articles(request.user, recommended_articles, request.GET.get('page'), log_paper_surf = False, tab_name = 'recommended')
        data['recommended_articles'] = recommended_articles
        data['paginated_recommended_articles'] = paginated_recommended_articles

    if additional_data is not None:
        data.update(additional_data)

    return shortcuts.render(request, 'index.html', data)