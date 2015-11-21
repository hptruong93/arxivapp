from datetime import datetime
import itertools

from django import shortcuts
from django import http
from django import template
from django.contrib import auth
from django.contrib.auth import decorators as auth_decorators
from django.core import urlresolvers
from django.core import paginator
from django.db import models as db_models


from main_app import models as main_app_models
# Create your views here.

MAX_SHORT_DESC_LEN = 200
MAX_COLUMN_DISPLAYED = 3
MAX_ARTICLE_DISPLAY = 20

def _n_group(l, n):
    return [ l[i:i+n] for i in range(0, len(l), n) ]

def _prepare_view_articles(articles, page_number):
    """
        Preprocess the articles with information to put on html template
        It is important to use pagination here and leverage the lazy nature of django model
        (i.e. only those articles on the current page are fetched from db)

        Without pagination, it would be impossible to fit all papers into memory and process them.
    """
    pagination = paginator.Paginator(articles, MAX_ARTICLE_DISPLAY)

    try:
        articles = pagination.page(page_number)
    except paginator.PageNotAnInteger: #Show first page
        articles = pagination.page(1)
    except paginator.EmptyPage: #Otherwise show last page if page out of range
        articles = paginator.page(pagination.num_pages)

    for article in articles:
        article.all_authors = article.authors.all()

    return _n_group(articles, MAX_COLUMN_DISPLAYED), articles

def _render_papers(request, articles, additional_data = None):
    articles, paginated_articles = _prepare_view_articles(articles, request.GET.get('page'))

    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles
    }

    if additional_data is not None:
        data.update(additional_data)

    return shortcuts.render(request, 'index.html', data)

def _to_login(request, message = ''):
    return shortcuts.render(request, 'login.html', {
            'message' : message
        })

###############################################################################################################################

@auth_decorators.login_required
def index(request):
    articles = main_app_models.Paper.objects.order_by('-created_date', 'title')
    return _render_papers(request, articles)

def signup(request):
    if request.method == 'POST':
        try:
            email = request.POST['user_email']
            password = request.POST['user_password']

            user = auth.models.User.objects.create_user(username=email, password=password, email = email)
            user.save()

            return http.HttpResponseRedirect(urlresolvers.reverse('login'))
        except KeyError:
            return shortcuts.render(request, 'signup.html')
    else:
        return shortcuts.render(request, 'signup.html')

def login(request, link = None):
    if request.method == 'POST':
        try:
            email = request.POST['user_email']
            password = request.POST['user_password']

            user = auth.authenticate(username=email, password=password, email = email)
            if user is not None:
                auth.login(request, user)

                if link is None or not link.startswith('?next='):
                    return http.HttpResponseRedirect(urlresolvers.reverse('index'))
                else:
                    return http.HttpResponseRedirect(link[len('?next='):])
            else:
                print "Failed to auth"
                return _to_login(request, 'Invalid credentials')
        except KeyError:
            return _to_login(request, 'Invalid credentials')
    else:
        return _to_login(request)

@auth_decorators.login_required
def author(request, author_id):
    author = shortcuts.get_object_or_404(main_app_models.Author, id = author_id)
    articles = main_app_models.Paper.objects.filter(authors__id = author_id).order_by('-created_date', 'title')
    return _render_papers(request, articles, {'header_message' : 'All articles by %s' % author})

@auth_decorators.login_required
def category(request, category_code):
    category = shortcuts.get_object_or_404(main_app_models.Category, code = category_code)
    articles = main_app_models.Paper.objects.filter(categories__code = category_code).order_by('-created_date', 'title')
    return _render_papers(request, articles, {'header_message' : 'All articles on %s' % category})

@auth_decorators.login_required
def paper(request, paper_id):
    paper = shortcuts.get_object_or_404(main_app_models.Paper, pk = paper_id)
    current_user = request.user

    MAX_HISTORY_PAPER = 100
    MAX_HISTORY_AUTHORS = 20
    MAX_HISTORY_CATEGORIES = 10

    def _remove_history(history_query, maximum_history_item):
        history_count = history_query.count()
        if history_count >= maximum_history_item:
            to_remove = history_query[maximum_history_item:] #Last object is the oldest
            for remove_history in to_remove:
                remove_history.delete()

    #paper
    paper_history_record, new_paper = main_app_models.PaperHistory.objects.get_or_create(user = current_user, paper = paper)
    paper_history_record.count += 1
    paper_history_record.save()

    query_paper_history = main_app_models.PaperHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(query_paper_history, MAX_HISTORY_PAPER)

    #author
    for author in paper.authors.all():
        history_record, created = main_app_models.AuthorHistory.objects.get_or_create(user = current_user, author = author)
        history_record.count += 1
        history_record.save()

    author_history = main_app_models.AuthorHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(author_history, MAX_HISTORY_AUTHORS)

    #category
    for category in paper.categories.all():
        history_record, created = main_app_models.CategoryHistory.objects.get_or_create(user = current_user, category = category)
        history_record.count += 1
        history_record.save()

    category_history = main_app_models.CategoryHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(category_history, MAX_HISTORY_CATEGORIES)


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
    #Custom action goes here. I.e. log user's activity
    return shortcuts.HttpResponseRedirect('http://www.arxiv.org/pdf/%s' % arxiv_id)

@auth_decorators.login_required
def history(request):
    current_user = request.user

    paper_history = main_app_models.PaperHistory.objects.filter(user = current_user).order_by('-last_access')
    articles = [paper_item.paper for paper_item in paper_history]
    articles, paginated_articles = _prepare_view_articles(articles, request.GET.get('page'))

    author_history = main_app_models.AuthorHistory.objects.filter(user = current_user).order_by('author__last_name', 'author__first_name')
    category_history = main_app_models.CategoryHistory.objects.filter(user = current_user).order_by('category__code')

    data = {
        'request' : request,
        'articles' : articles,
        'paginated_articles' : paginated_articles,
        'authors' : author_history,
        'categories' : category_history
    }
    return shortcuts.render(request, 'history.html', data)

@auth_decorators.login_required
def search(request):
    try:
        search_value = request.POST['search_value']
        print "Searching for %s" % search_value
        articles_query = main_app_models.Paper.objects.filter(title__icontains = search_value).order_by('-created_date', 'title')
        articles, paginated_articles = _prepare_view_articles(articles_query, request.GET.get('page'))

        authors = main_app_models.Author.objects.filter(db_models.Q(first_name__icontains = search_value) | db_models.Q(last_name__icontains = search_value))
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
            }
        }

        return shortcuts.render(request, 'search.html', data)
    except KeyError as e:
        print "Unable to find search term"
        return index(request)
    