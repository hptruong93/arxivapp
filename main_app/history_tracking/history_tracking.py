from main_app import models as main_app_models


MAX_HISTORY_PAPER = 100
MAX_HISTORY_AUTHORS = 20
MAX_HISTORY_CATEGORIES = 10

def _remove_history(history_query, maximum_history_item):
    history_count = history_query.count()
    if history_count >= maximum_history_item:
        to_remove = history_query[maximum_history_item:] #Last object is the oldest
        for remove_history in to_remove:
            remove_history.delete()

def log_paper(current_user, paper):
    paper_history_record, new_paper = main_app_models.PaperHistory.objects.get_or_create(user = current_user, paper = paper)
    paper_history_record.count += 1
    paper_history_record.save()

    query_paper_history = main_app_models.PaperHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(query_paper_history, MAX_HISTORY_PAPER)

    return paper_history_record, new_paper

def log_author(author_id):
    pass

def log_authors(current_user, paper):
    for author in paper.authors.all():
        history_record, new_author = main_app_models.AuthorHistory.objects.get_or_create(user = current_user, author = author)
        history_record.count += 1
        history_record.save()

    author_history = main_app_models.AuthorHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(author_history, MAX_HISTORY_AUTHORS)

def log_categories(current_user, paper):
    for category in paper.categories.all():
        history_record, new_category = main_app_models.CategoryHistory.objects.get_or_create(user = current_user, category = category)
        history_record.count += 1
        history_record.save()

    category_history = main_app_models.CategoryHistory.objects.filter(user = current_user).order_by('-last_access')
    _remove_history(category_history, MAX_HISTORY_CATEGORIES)