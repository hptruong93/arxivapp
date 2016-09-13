from django import shortcuts
from django.core import paginator

import time

from main_app import models as main_app_models
from main_app.history_tracking import history_tracking
from main_app.view_filters_sorts import paper_filter_sorts
from main_app import central_config as config
from main_app.utils import utils_general

from main_app import recommendation_interface

class TabData(object):
    def __init__(self, articles, sort_strategy = None, log_paper_surf = True):
        super(TabData, self).__init__()
        self.articles = articles
        self.sort_strategy = sort_strategy
        self.log_paper_surf = log_paper_surf

class AdditionalData(object):
    """
        Containing any additional information used for rendering (e.g. show/hide certain elements), title, and other customizations)
    """
    def __init__(self, header_message = None, filters_sorts = None, display_filter = True):
        super(AdditionalData, self).__init__()
        self.header_message = header_message
        self.filters_sorts = filters_sorts
        self.display_filter = display_filter

    def to_dict(self):
        output = {}
        if self.header_message:
            output['header_message'] = self.header_message

        if self.filters_sorts:
            output['filters_sorts'] = self.filters_sorts

        output['display_filter'] = self.display_filter
        return output


def general_filter_check(request, default_filter = False, filter_type = 'main'):
    filter_args = []
    filter_dict = {}
    order_by_fields = ['-created_date', 'title']

    filter_data = {}
    if request.method == "POST":
        filter_data = paper_filter_sorts.filter_paper(request, filter_args, filter_dict, order_by_fields, filter_type)
    elif default_filter:
        filter_data = paper_filter_sorts.filter_paper_default(request, filter_args, filter_dict, order_by_fields, filter_type)

    return filter_args, filter_dict, order_by_fields, filter_data

def query_filter(query, filter_args, filter_dict, order_by_fields):
    """
        Apply filter for a query based on the filter args and dict.
        Also apply ordering for a query based on the list of fields.
        Return the query itself, with applied filters and ordering.
    """
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
        if len(article.ordered_authors) == 0:
            article.all_authors = article.authors.all()
        else:
            all_authors = [int(author_id) for author_id in article.ordered_authors.split(',')]
            all_authors = map(lambda author_id : shortcuts.get_object_or_404(main_app_models.Author, id = author_id), all_authors)
            article.all_authors = all_authors

        article.all_categories = article.categories.all()

    return utils_general._n_group(sorted_articles, config.MAX_COLUMN_DISPLAYED), sorted_articles, surf_group

def render_papers(request, articles_data, cross_list_data = None, replacement_data = None, recommended_articles_data = None, additional_data = None):
    do_log = articles_data.log_paper_surf
    articles = articles_data.articles
    sort_strategy = articles_data.sort_strategy

    articles, paginated_articles, surf_group = prepare_view_articles(request.user, articles, request.GET.get('page'), tab_name = 'latest', sort_strategy = sort_strategy, log_paper_surf = do_log)
    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles,
        'latest_surf_group': surf_group.id if surf_group else ""
    }

    if cross_list_data is not None:
        do_log = cross_list_data.log_paper_surf
        cross_list = cross_list_data.articles
        sort_strategy = cross_list_data.sort_strategy

        cross_list_articles, paginated_cross_list_articles, surf_group = prepare_view_articles(request.user, cross_list, request.GET.get('page'), tab_name = 'cross_list', sort_strategy = sort_strategy, log_paper_surf= do_log)
        data['cross_list_articles'] = cross_list_articles
        data['paginated_cross_list_articles'] = paginated_cross_list_articles
        data['cross_list_surf_group'] = surf_group.id

    if replacement_data is not None:
        do_log = replacement_data.log_paper_surf
        replacement = replacement_data.articles
        sort_strategy = replacement_data.sort_strategy

        replacement_articles, paginated_replacement_articles, surf_group = prepare_view_articles(request.user, replacement, request.GET.get('page'), tab_name = 'replacement', sort_strategy = sort_strategy, log_paper_surf = do_log)
        data['replacement_articles'] = replacement_articles
        data['paginated_replacement_articles'] = paginated_replacement_articles
        data['replacement_surf_group'] = surf_group.id

    if recommended_articles_data is not None:
        do_log = recommended_articles_data.log_paper_surf
        recommended_articles = recommended_articles_data.articles

        recommended_articles, paginated_recommended_articles, _ = prepare_view_articles(request.user, recommended_articles, request.GET.get('page'), tab_name = 'recommended', log_paper_surf = do_log)
        data['recommended_articles'] = recommended_articles
        data['paginated_recommended_articles'] = paginated_recommended_articles

    if additional_data is not None:
        data.update(additional_data.to_dict())

    return shortcuts.render(request, 'index.html', data)
