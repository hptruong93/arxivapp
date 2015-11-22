from main_app import models


MAX_HISTORY_PAPER = 100
MAX_HISTORY_PAPER_SURF = 1000
MAX_HISTORY_AUTHORS = 20
MAX_HISTORY_AUTHOR_FOCUS = 100
MAX_HISTORY_CATEGORIES = 10
MAX_HISTORY_CATEGORIES_FOCUS = 20
MAX_HISTORY_SEARCH = 200

def _remove_history(history_query, maximum_history_item):
    history_count = history_query.count()
    if history_count >= maximum_history_item:
        to_remove = history_query[maximum_history_item:] #Last object is the oldest
        for remove_history in to_remove:
            remove_history.delete()

def _add_history_record(model, current_user, **kwargs):
    data = {
        'user' : current_user,
    }
    data.update(kwargs)

    history_record, new_entry = model.objects.get_or_create(**data)
    history_record.count += 1
    history_record.save()

    return history_record, new_entry

def log_paper_surf(current_user, papers):
    for paper in papers:
        _add_history_record(models.PaperSurfHistory, current_user, paper = paper)

    paper_surf_history = models.PaperSurfHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(paper_surf_history, MAX_HISTORY_PAPER_SURF)

def log_paper(current_user, paper):
    paper_history_record, new_paper = _add_history_record(models.PaperHistory, current_user, paper = paper)
    query_paper_history = models.PaperHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(query_paper_history, MAX_HISTORY_PAPER)

    return paper_history_record, new_paper

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
