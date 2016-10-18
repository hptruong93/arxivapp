from django import shortcuts
from django.core import paginator

import time
from datetime import datetime

from main_app import models as main_app_models
from main_app.history_tracking import history_tracking
from main_app.view_filters_sorts import paper_filter_sorts
from main_app import central_config as config
from main_app.utils import utils_date
from main_app.utils import utils_general

from main_app import recommendation_interface

class TabData(object):
    def __init__(self, articles, sort_strategy = None, log_paper_surf = True):
        super(TabData, self).__init__()
        self.articles = articles
        self.sort_strategy = sort_strategy
        self.log_paper_surf = log_paper_surf

class FilterDisplayed(object):
    """
        Containing any information about which filter to display. Default constructor displays all filters.
    """
    def __init__(self, category = True, date = True, make_default_choice = True):
        super(FilterDisplayed, self).__init__()
        self.category = category
        self.date = date
        self.make_default_choice = make_default_choice # The checkbox to allow user to make this filter default

    def to_dict(self):
        return {
            'category' : self.category,
            'date' : self.date,
            'make_default_choice' : self.make_default_choice
        }

class AdditionalData(object):
    """
        Containing any additional information used for rendering (e.g. show/hide certain elements), title, and other customizations)
    """
    def __init__(self, header_message = None, tab_names = None, filters_sorts = None, displayed_filters = FilterDisplayed(), section_message = None, info_message = None):
        super(AdditionalData, self).__init__()
        self.header_message = header_message # Name for the page, shown as header on top
        self.tab_names = tab_names # List of names of the tabs in the page
        self.filters_sorts = filters_sorts
        self.displayed_filters = displayed_filters # Information about which filter to be displayed
        self.section_message = section_message # Small message under header to inform user of something
        self.info_message = info_message

    def to_dict(self):
        output = {}
        if self.header_message:
            output['header_message'] = self.header_message

        if self.tab_names:
            output['tab_names'] = self.tab_names

        if self.filters_sorts:
            output['filters_sorts'] = self.filters_sorts

        output['displayed_filters'] = self.displayed_filters.to_dict()

        if self.section_message:
            output['section_message'] = self.section_message

        if self.info_message:
            output['info_message'] = self.info_message

        return output

########################################################################################################################################
########################################################################################################################################
########################################################################################################################################

def get_page_number(request):
    """
        Retrieve the page number from the request.
        This prioritizes page number from the POST filtering parameter over the GET request parameter.
    """
    page_number = request.GET.get('page')
    if not page_number:
        page_number = request.POST.get('filter_page')
    return page_number

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

def render_papers(request, articles_data, tab1_data = None, tab2_data = None, recommended_articles_data = None, additional_data = None):
    """
        Render the page with the main tab and optional cross list, replacement and recommendation tabs.
        Construct the appropriate data object to pass on to template for html rendering.
    """
    page_number = get_page_number(request)

    do_log = articles_data.log_paper_surf
    articles = articles_data.articles
    sort_strategy = articles_data.sort_strategy

    tab_name = additional_data.tab_names[0] if additional_data and additional_data.tab_names else 'latest'
    articles, paginated_articles, surf_group = prepare_view_articles(request.user, articles, page_number, tab_name = tab_name, sort_strategy = sort_strategy, log_paper_surf = do_log)
    # Retrieve user last login, which is considered to be the last date that is not today on which the user was active, or today if the former date does not exist
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        recent_activities = main_app_models.UserLastActivity.objects.filter(user = request.user, last_activity__lt = today).order_by('-last_activity')
        last_login = recent_activities[0]
        last_login = last_login.last_activity
    except: # Does not exist, just put today instead
        import traceback
        traceback.print_exc()
        last_login = today

    # Generate common data object
    data = {
        'request' : request,
        'user_last_login' : utils_date.date_to_string(last_login),
        'articles' : articles,
        'paginated_articles' : paginated_articles,
        'latest_surf_group': surf_group.id if surf_group else ""
    }

    if tab1_data is not None:
        do_log = tab1_data.log_paper_surf
        cross_list = tab1_data.articles
        sort_strategy = tab1_data.sort_strategy

        tab_name = additional_data.tab_names[1] if additional_data and additional_data.tab_names else 'cross_list'
        tab1_articles, paginated_tab1_articles, surf_group = prepare_view_articles(request.user, cross_list, page_number, tab_name = tab_name, sort_strategy = sort_strategy, log_paper_surf= do_log)
        data['tab1_articles'] = tab1_articles
        data['paginated_tab1_articles'] = paginated_tab1_articles
        data['tab1_surf_group'] = surf_group.id

    if tab2_data is not None:
        do_log = tab2_data.log_paper_surf
        replacement = tab2_data.articles
        sort_strategy = tab2_data.sort_strategy

        tab_name = additional_data.tab_names[2] if additional_data and additional_data.tab_names else 'replacement'
        tab2_articles, paginated_tab2_articles, surf_group = prepare_view_articles(request.user, replacement, page_number, tab_name = tab_name, sort_strategy = sort_strategy, log_paper_surf = do_log)
        data['tab2_articles'] = tab2_articles
        data['paginated_tab2_articles'] = paginated_tab2_articles
        data['tab2_surf_group'] = surf_group.id

    if recommended_articles_data is not None:
        do_log = recommended_articles_data.log_paper_surf
        recommended_articles = recommended_articles_data.articles

        tab_name = self.additional_data.tab_names[3] if self.additional_data and self.additional_data.tab_names else 'recommended'
        recommended_articles, paginated_recommended_articles, _ = prepare_view_articles(request.user, recommended_articles, page_number, tab_name = tab_name, log_paper_surf = do_log)
        data['recommended_articles'] = recommended_articles
        data['paginated_recommended_articles'] = paginated_recommended_articles

    if additional_data is not None:
        data.update(additional_data.to_dict())

    return shortcuts.render(request, 'index.html', data)
