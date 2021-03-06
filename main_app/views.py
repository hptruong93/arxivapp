from datetime import datetime
import time
import itertools

from django import shortcuts
from django import http
from django import template
from django.contrib import auth
from django.contrib.auth import decorators as auth_decorators
from django.core import urlresolvers
from django.core import paginator
from django.db import models as db_models
from django.db import IntegrityError
from django.db.models import Sum
from django.views.decorators.http import require_GET, require_POST

from main_app import models as main_app_models
from main_app.history_tracking import history_tracking
from main_app.view_filters_sorts import paper_filter_sorts
from main_app import central_config as config
from main_app import view_renderer
from main_app import recommendation_interface
from main_app.utils import utils_general
from main_app.utils import utils_date

# Create your views here.

def _to_login(request, message = ''):
    return shortcuts.render(request, 'login.html', {
            'message' : message
        })

def _to_signup(request, message = ''):
    return shortcuts.render(request, 'signup.html', {
            'message' : message
        })

###############################################################################################################################

def signup(request):
    if request.method != 'POST':
        return shortcuts.render(request, 'signup.html')

    try:
        email = request.POST['user_email']
        username = email[:config.MAX_USERNAME_LEN]
        password = request.POST['user_password']

        user = auth.models.User.objects.create_user(username=username, password=password, email = email)
        user.save()

        return http.HttpResponseRedirect(urlresolvers.reverse('arxiv_login'))
    except KeyError as e:
        return shortcuts.render(request, 'signup.html')
    except IntegrityError:
        return _to_signup(request, "Username existed...")


def login(request, link = None):
    if request.method != 'POST':
        return _to_login(request)

    try:
        email = request.POST['user_email']
        username = email[:config.MAX_USERNAME_LEN]
        password = request.POST['user_password']

        user = auth.authenticate(username=username, password=password, email = email)
        if user is None:
            print "Failed to auth"
            return _to_login(request, 'Invalid credentials')

        auth.login(request, user)

        if link is None or not link.startswith('?next='):
            return http.HttpResponseRedirect(urlresolvers.reverse('index'))
        else:
            return http.HttpResponseRedirect(link[len('?next='):])

    except KeyError:
        return _to_login(request, 'Invalid credentials')


def logout(request):
    auth.logout(request)
    return http.HttpResponseRedirect(urlresolvers.reverse('index'))

###############################################################################################################################
###############################################################################################################################
###############################################################################################################################

@auth_decorators.login_required
def browse(request):
    """
        Browse all papers with filtering parameters.
    """
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
    order_by_fields = ['-created_date']
    articles = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)[:config.MAX_ARTICLE_SORTING]

    # Also sort papers
    sort_strategy, articles = recommendation_interface.sort(request.user, articles)
    articles_data = view_renderer.TabData(articles, sort_strategy, True)
    return view_renderer.render_papers( request,
                                        articles_data, None, None, None,
                                        additional_data = view_renderer.AdditionalData(
                                                                        None,
                                                                        tab_names = ['Paper search'],
                                                                        filters_sorts = filter_data,
                                                                        displayed_filters = view_renderer.FilterDisplayed(make_default_choice = False),
                                                                        section_message = 'Paper search',
                                                                        info_message = 'Limited to a maximum {0} papers.\n'.format(config.MAX_ARTICLE_SORTING)))

@auth_decorators.login_required
def index(request):
    """
        Only show papers from today, in the following tabs:
        1) Latest
        2) Cross list
        3) Replacement
        4) (Currently disabled) Recommended

        Only allow filtering by category
    """
    # First update the latest activity for this user.
    latest_activity = main_app_models.UserLastActivity()
    latest_activity.user = request.user
    latest_activity.last_activity = datetime.now()
    latest_activity.save()

    today = utils_date.get_today()

    # Retrieve papers for latest tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = 'main')
    # Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': True })
    order_by_fields = ['-arxiv_id']
    articles = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)

    # No longer needed since merged latest and cross list tabs
    # Also sort papers in this tab
    # sort_strategy, articles = recommendation_interface.sort(request.user, articles)
    # articles_data = view_renderer.TabData(articles, sort_strategy)

    # Retrieve papers for cross_list tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = 'cross_list')
    # Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    #  filter_dict.update({ 'created_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': True })
    order_by_fields = ['-arxiv_id']
    cross_list = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)

    # No longer needed since merged latest and cross list tabs
    # Also sort papers in this tab
    # sort_strategy, cross_list = recommendation_interface.sort(request.user, cross_list)
    # cross_list_data = view_renderer.TabData(cross_list, sort_strategy)

    # Merging two tabs
    articles = list(articles) + list(cross_list) # Since there are a few paper in home page, we can fetch all of them without worrying about performance.
    # Sort the merged articles
    sort_strategy, articles = recommendation_interface.sort(request.user, articles)
    articles_data = view_renderer.TabData(articles, sort_strategy)


    # Retrieve papers for replacement tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = 'replacement')
    # Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': False })
    replacement = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)

    # Also sort papers in this tab
    sort_strategy, replacement = recommendation_interface.sort(request.user, replacement)
    replacement_data = view_renderer.TabData(replacement, sort_strategy)

    # Retrieve papers for recommended tab
    # recommended_articles = recommendation_interface.index(request.user)
    # recommended_articles_data = view_renderer.TabData(recommended_articles, None, False)
    recommended_articles_data = None # Disabled for now

    return view_renderer.render_papers(request, articles_data, None, replacement_data, recommended_articles_data,
                                        additional_data = view_renderer.AdditionalData( None,
                                                                                        filters_sorts = filter_data,
                                                                                        section_message = 'Today\'s papers',
                                                                                        displayed_filters = view_renderer.FilterDisplayed(date = False)))

@auth_decorators.login_required
def author(request, author_id):
    author = shortcuts.get_object_or_404(main_app_models.Author, id = author_id)
    history_tracking.log_author_focus(request.user, author)

    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
    articles = view_renderer.query_filter(main_app_models.Paper.objects.filter(authors__id = author_id), filter_args, filter_dict, order_by_fields)

    return view_renderer.render_papers(request, view_renderer.TabData(articles, None, False),
                                        additional_data = view_renderer.AdditionalData('All articles by %s' % author,
                                                                                        filters_sorts = filter_data,
                                                                                        displayed_filters = view_renderer.FilterDisplayed(
                                                                                                make_default_choice = False),
                                                                                        section_message = 'Author'))

@auth_decorators.login_required
def category(request, category_code):
    category = shortcuts.get_object_or_404(main_app_models.Category, code = category_code)
    history_tracking.log_category_focus(request.user, category)

    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
    articles = view_renderer.query_filter(main_app_models.Paper.objects.filter(categories__code = category_code), filter_args, filter_dict, order_by_fields)
    return view_renderer.render_papers(request, view_renderer.TabData(articles, None, False),
                                        additional_data = view_renderer.AdditionalData('All articles in %s' % category,
                                                                                        filters_sorts = filter_data,
                                                                                        displayed_filters = view_renderer.FilterDisplayed(
                                                                                                category = False,
                                                                                                make_default_choice = False),
                                                                                        section_message = 'Category'))

@auth_decorators.login_required
def paper(request, paper_id):
    paper = shortcuts.get_object_or_404(main_app_models.Paper, pk = paper_id)
    current_user = request.user

    surf_group = None
    if request.method == "GET":
        if 'surf_group' in request.GET:
            surf_group_id = request.GET['surf_group']
            surf_group = shortcuts.get_object_or_404(main_app_models.PaperSurfHistory, pk = int(surf_group_id))

    if not surf_group: # Check for empty string
        surf_group = None

    paper_history_record, new_paper = history_tracking.log_paper(current_user, paper, surf_group)
    history_tracking.log_authors(current_user, paper)
    history_tracking.log_categories(current_user, paper)

    # Check if paper has been bookmarked
    is_bookmarked = main_app_models.PaperBookmark.objects.filter(user = current_user, paper = paper).count() > 0

    data = {
        'request' : request,
        'paper' : paper,
        'history' : {
            'seen' : not new_paper,
            'last_access' : paper_history_record.last_access
        },
        'is_bookmarked' : is_bookmarked,
        'authors' : paper.authors.all(),
        'categories' : paper.categories.all()
    }

    return shortcuts.render(request, 'paper.html', data)

@auth_decorators.login_required
def pdf(request, arxiv_id):
    paper = shortcuts.get_object_or_404(main_app_models.Paper, pk = arxiv_id)
    history_tracking.log_full_paper_view(request.user, paper)
    return shortcuts.HttpResponseRedirect('http://www.arxiv.org/pdf/%s' % arxiv_id)

@auth_decorators.login_required
def arxiv_abstract(request, arxiv_id):
    paper = shortcuts.get_object_or_404(main_app_models.Paper, pk = arxiv_id)
    history_tracking.log_abstract_paper_view(request.user, paper)
    return shortcuts.HttpResponseRedirect('http://www.arxiv.org/abs/%s' % arxiv_id)

@auth_decorators.login_required
def history(request):
    current_user = request.user
    filter_args = []
    filter_dict = {}
    order_by_fields = ['-last_access']

    filter_data = {}
    if request.method == "POST":
        filter_data = paper_filter_sorts.filter_paper_history(request, filter_args, filter_dict, order_by_fields)

    paper_history = view_renderer.query_filter(main_app_models.PaperHistory.objects.filter(user = current_user), filter_args, filter_dict, order_by_fields)
    articles = list(set(paper_item.paper for paper_item in paper_history))

    articles, paginated_articles, _ = view_renderer.prepare_view_articles(current_user, articles, view_renderer.get_page_number(request), log_paper_surf = False)

    author_history = main_app_models.AuthorHistory.objects.filter(user = current_user)
    author_history = author_history.values('author__id', 'author__last_name', 'author__first_name')
    author_history = author_history.annotate(seen_count=Sum('count')).order_by('author__last_name', 'author__first_name')

    category_history = main_app_models.CategoryHistory.objects.filter(user = current_user)
    category_history = category_history.values('category__code').annotate(seen_count=Sum('count')).order_by('category__code')

    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles,
        'authors' : author_history,
        'categories' : category_history,
        'filters_sorts' : filter_data,
    }

    return shortcuts.render(request, 'history.html', data)

@auth_decorators.login_required
@require_POST
def bookmark(request): # The bookmark action
    current_user = request.user
    arxiv_ids = request.POST['arxiv_ids'].split(',')
    action = request.POST['action']
    next_page = request.POST.get('next_page', None)

    if action == "add":
        papers = [shortcuts.get_object_or_404(main_app_models.Paper, pk = arxiv_id) for arxiv_id in arxiv_ids]

        for paper in papers:
            bookmark_object, is_new = main_app_models.PaperBookmark.objects.get_or_create(user = current_user, paper = paper)

    else: # Delete
        main_app_models.PaperBookmark.objects.filter(user = current_user, paper__pk__in = arxiv_ids).delete()

    if next_page is None:
        # Redirect to the first paper page
        return http.HttpResponseRedirect(urlresolvers.reverse('paper', kwargs={'paper_id': arxiv_ids[0]}))
    else:
        return http.HttpResponseRedirect(next_page)


@auth_decorators.login_required
def bookmarks(request): # The bookmark page
    current_user = request.user
    filter_args = []
    filter_dict = {}
    order_by_fields = ['-created_time']

    articles = view_renderer.query_filter(main_app_models.PaperBookmark.objects.filter(user = current_user), filter_args, filter_dict, order_by_fields)
    articles = [article.paper for article in articles]

    articles, paginated_articles, _ = view_renderer.prepare_view_articles(current_user, articles, view_renderer.get_page_number(request), log_paper_surf = False)

    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles,
    }

    return shortcuts.render(request, 'bookmarks.html', data)


@auth_decorators.login_required
def search(request):
    current_user = request.user
    try:
        search_value = request.POST['search_value']
        history_tracking.log_search(current_user, search_value)

        filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
        articles_query = view_renderer.query_filter(main_app_models.Paper.objects.filter(title__icontains = search_value), filter_args, filter_dict, order_by_fields)
        articles, paginated_articles, _ = view_renderer.prepare_view_articles(current_user, articles_query, view_renderer.get_page_number(request), log_paper_surf = False)

        authors = main_app_models.Author.objects.filter(full_name__icontains = search_value)
        categories = main_app_models.Category.objects.filter(db_models.Q(code__icontains = search_value) | db_models.Q(name__icontains = search_value))

        data = {
            'request' : request,
            'articles' : articles,
            'paginated_articles' : paginated_articles,
            'authors' : authors,
            'categories' : categories,
            'count' : {
                'articles' : articles_query.count(),
                'authors' : len(authors),
                'categories' : len(categories)
            },
            'search_value' : search_value,
            'filters_sorts' : filter_data,
        }

        return shortcuts.render(request, 'search.html', data)
    except KeyError as e:
        print "Unable to find search term"
        return index(request)
