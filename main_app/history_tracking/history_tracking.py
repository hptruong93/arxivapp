from main_app import models


MAX_HISTORY_PAPER = 1000
MAX_HISTORY_PAPER_SURF = 10000
MAX_HISTORY_AUTHORS = 200
MAX_HISTORY_AUTHOR_FOCUS = 1000
MAX_HISTORY_CATEGORIES = 100
MAX_HISTORY_CATEGORIES_FOCUS = 200
MAX_HISTORY_SEARCH = 2000
MAX_HISTORY_FULL_PAPER_VIEW = 1000

def _remove_history(history_query, maximum_history_item):
    """
        Remove the oldest history entries from the record so that the number of entries
        is less than or equal to maximum_history_item
    """
    history_count = history_query.count()
    if history_count < maximum_history_item:
        return
    to_remove = history_query[maximum_history_item:] #Last object is the oldest
    for remove_history in to_remove:
        remove_history.delete()

def _add_history_record(model, current_user, **kwargs):
    data = {
        'user' : current_user,
        'count' : 1
    }
    data.update(kwargs)

    history_record = model(**data)
    history_record.save()

    return history_record

def log_paper_surf(current_user, papers, page_number, tab_name, strategy):
    surf_group = _add_history_record(models.PaperSurfHistory, current_user, page_number = page_number, tab_name = tab_name, strategy = strategy)

    for index, paper in enumerate(papers):
        indexed_paper = models.IndexedPaper(paper = paper, in_page_index = index, surf_group = surf_group)
        indexed_paper.save()

    paper_surf_history = models.PaperSurfHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(paper_surf_history, MAX_HISTORY_PAPER_SURF)
    return surf_group

def log_paper(current_user, paper, surf_group):
    is_new = models.PaperHistory.objects.filter(user = current_user, paper = paper).count() == 0
    paper_history_record = _add_history_record(models.PaperHistory, current_user, paper = paper, surf_group = surf_group)
    query_paper_history = models.PaperHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(query_paper_history, MAX_HISTORY_PAPER)

    return paper_history_record, is_new

def log_author_focus(current_user, author):
    _add_history_record(models.AuthorFocusHistory, current_user, author = author)
    author_history = models.AuthorFocusHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(author_history, MAX_HISTORY_AUTHOR_FOCUS)


def log_authors(current_user, paper):
    for author in paper.authors.all():
        _add_history_record(models.AuthorHistory, current_user, author = author)

    author_history = models.AuthorHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(author_history, MAX_HISTORY_AUTHORS)

def log_category_focus(current_user, category):
    _add_history_record(models.CategoryFocusHistory, current_user, category = category)
    author_history = models.CategoryFocusHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(author_history, MAX_HISTORY_CATEGORIES_FOCUS)

def log_categories(current_user, paper):
    for category in paper.categories.all():
        _add_history_record(models.CategoryHistory, current_user, category = category)

    category_history = models.CategoryHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(category_history, MAX_HISTORY_CATEGORIES)

def log_search(current_user, search_term):
    _add_history_record(models.SearchHistory, current_user, search_term = search_term)
    search_history = models.SearchHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(search_history, MAX_HISTORY_SEARCH)

def log_full_paper_view(current_user, paper):
    _add_history_record(models.FullPaperViewHistory, current_user, paper = paper)
    full_paper_view_history = models.FullPaperViewHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(full_paper_view_history, MAX_HISTORY_FULL_PAPER_VIEW)
