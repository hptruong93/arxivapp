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
    if request.method == 'POST':
        return shortcuts.render(request, 'signup.html')

    try:
        email = request.POST['user_email']
        username = email[:config.MAX_USERNAME_LEN]
        password = request.POST['user_password']

        user = auth.models.User.objects.create_user(username=username, password=password, email = email)
        user.save()

        return http.HttpResponseRedirect(urlresolvers.reverse('login'))
    except KeyError:
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

# @auth_decorators.login_required
# def original_index(request):
#     filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True)
#     articles = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)
#     recommended_articles = recommendation_interface.index(request.user)

#     return view_renderer.render_papers(request, articles, recommended_articles, additional_data = {'filters_sorts' : filter_data})

@auth_decorators.login_required
def index(request):
    today = utils_date.get_today()


    start = time.time()

    #Retrieve papers for latest tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = 'main')
    #Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': True })
    order_by_fields = ['arxiv_id']
    articles = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)
    print articles.query

    print "View Stage 1 took {0}s".format(time.time() - start)
    start = time.time()

    #Also sort papers in this tab
    sort_strategy, articles = recommendation_interface.sort(request.user, articles)
    articles_data = view_renderer.TabData(articles, sort_strategy)

    print "View Stage 2 took {0}s".format(time.time() - start)
    start = time.time()

    #Retrieve papers for cross_list tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = 'cross_list')
    #Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    # filter_dict.update({ 'created_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': True })
    order_by_fields = ['arxiv_id']
    cross_list = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)
    print cross_list.query

    print "View Stage 3 took {0}s".format(time.time() - start)
    start = time.time()

    #Also sort papers in this tab
    sort_strategy, cross_list = recommendation_interface.sort(request.user, cross_list)
    cross_list_data = view_renderer.TabData(cross_list, sort_strategy)

    print "View Stage 4 took {0}s".format(time.time() - start)
    start = time.time()


    #Retrieve papers for replacement tab
    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request, default_filter = True, filter_type = '')
    #Only looking for papers from yesterday
    filter_dict.update({ 'last_resigered_date__gte': today })
    filter_dict.update({ 'updated_date__isnull': False })
    replacement = view_renderer.query_filter(main_app_models.Paper.objects, filter_args, filter_dict, order_by_fields)
    print replacement.query
    
    print "View Stage 5 took {0}s".format(time.time() - start)
    start = time.time()

    #Also sort papers in this tab
    sort_strategy, replacement = recommendation_interface.sort(request.user, replacement)
    replacement_data = view_renderer.TabData(replacement, sort_strategy)

    print "View Stage 6 took {0}s".format(time.time() - start)
    start = time.time()


    #Retrieve papers for recommended tab
    # recommended_articles = recommendation_interface.index(request.user)
    # recommended_articles_data = view_renderer.TabData(recommended_articles, None)
    recommended_articles_data = None #Disabled for now

    return view_renderer.render_papers(request, articles_data, cross_list_data, replacement_data, recommended_articles_data, additional_data = {'filters_sorts' : filter_data})

@auth_decorators.login_required
def author(request, author_id):
    return http.HttpResponseNotFound('Not currently supported')

    author = shortcuts.get_object_or_404(main_app_models.Author, id = author_id)
    history_tracking.log_author_focus(request.user, author)

    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
    articles = view_renderer.query_filter(main_app_models.Paper.objects.filter(authors__id = author_id), filter_args, filter_dict, order_by_fields)
    return view_renderer.render_papers(request, view_renderer.TabData(articles), additional_data = {'header_message' : 'All articles by %s' % author, 'filters_sorts' : filter_data})

@auth_decorators.login_required
def category(request, category_code):
    return http.HttpResponseNotFound('Not currently supported')

    category = shortcuts.get_object_or_404(main_app_models.Category, code = category_code)
    history_tracking.log_category_focus(request.user, category)

    filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
    articles = view_renderer.query_filter(main_app_models.Paper.objects.filter(categories__code = category_code), filter_args, filter_dict, order_by_fields)
    return view_renderer.render_papers(request, view_renderer.TabData(articles), additional_data = {'header_message' : 'All articles in %s' % category, 'filters_sorts' : filter_data})

@auth_decorators.login_required
def paper(request, paper_id):
    paper = shortcuts.get_object_or_404(main_app_models.Paper, pk = paper_id)
    current_user = request.user

    surf_group = None
    if request.method == "GET":
        if 'surf_group' in request.GET:
            surf_group_id = request.GET['surf_group']
            surf_group = shortcuts.get_object_or_404(main_app_models.PaperSurfHistory, pk = int(surf_group_id))

    paper_history_record, new_paper = history_tracking.log_paper(current_user, paper, surf_group)
    history_tracking.log_authors(current_user, paper)
    history_tracking.log_categories(current_user, paper)

    data = {
        'request' : request,
        'paper' : paper,
        'history' : {
            'seen' : not new_paper,
            'last_access' : paper_history_record.last_access
        },
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

    articles, paginated_articles, _ = view_renderer.prepare_view_articles(current_user, articles, request.GET.get('page'), log_paper_surf = False)
    
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
def search(request):
    return http.HttpResponseNotFound('Not currently supported')

    current_user = request.user
    try:
        search_value = request.POST['search_value']
        history_tracking.log_search(current_user, search_value)

        filter_args, filter_dict, order_by_fields, filter_data = view_renderer.general_filter_check(request)
        articles_query = view_renderer.query_filter(main_app_models.Paper.objects.filter(title__icontains = search_value), filter_args, filter_dict, order_by_fields)
        articles, paginated_articles = view_renderer.prepare_view_articles(current_user, articles_query, request.GET.get('page'))

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
    