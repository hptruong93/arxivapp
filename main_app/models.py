from django.contrib.auth import models as auth_models
from django.db import models
import abstract_models

# Create your models here.

class UserFilterSort(models.Model):
    user = models.ForeignKey(auth_models.User)
    
    title = models.CharField(max_length = 200, null = True)

    author_full_name = models.CharField(max_length = 50, null = True)
    category = models.CharField(max_length = 50, null = True)

    from_date = models.DateTimeField(null = True)
    to_date = models.DateTimeField(null = True)

    sort_by_1 = models.CharField(max_length = 20, null = True)
    sort_by_2 = models.CharField(max_length = 20, null = True)

    is_default = models.BooleanField(default = False)

    def save(self, *args, **kwargs):
        if self.is_default:
            try:
                default_filter = UserFilterSort.objects.get(is_default = True)
                if self != default_filter:
                    default_filter.is_default = False
                    default_filter.save()
            except UserFilterSort.DoesNotExist:
                pass
        super(UserFilterSort, self).save(*args, **kwargs)


class Author(models.Model):
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=50, null = True)
    last_name = models.CharField(max_length=50)

    full_name = models.CharField(max_length = 300)

    def save(self, *args, **kwargs):
        self.full_name = self.first_name + ' ' + self.last_name
        super(Author, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.full_name

class Category(models.Model):
    code = models.CharField(max_length=20, primary_key = True)
    name = models.CharField(max_length=100, null = True)

    def __unicode__(self):
        return self.code

class Paper(models.Model):
    arxiv_id = models.CharField(max_length=30, primary_key = True)
    created_date = models.DateTimeField(null = True)
    updated_date = models.DateTimeField(null = True)
    
    categories = models.ManyToManyField(Category) 
    journal_ref = models.CharField(max_length = 1000, null = True)
    
    title = models.CharField(max_length=400)
    authors = models.ManyToManyField(Author)
    abstract = models.CharField(max_length=5000)
    link_full_text_pdf = models.CharField(max_length=700, null = True)

    def __unicode__(self):
        return self.title

class PaperHistory(abstract_models.AbstractUserHistory):
    """
        Logged when user clicks on a specific paper
    """
    paper = models.ForeignKey(Paper)

class PaperSurfHistory(abstract_models.AbstractUserHistory):
    """
        Logged when user browse papers and this one shows up in the browsing screen
        The difference with regular PaperHistory is that the user does not have to click
        on the paper for this to be logged
    """
    paper = models.ForeignKey(Paper)
    page_number = models.IntegerField(default = 0, null = False)
    in_page_index = models.IntegerField(default = 0, null = False)

class AuthorFocusHistory(abstract_models.AbstractUserHistory):
    """
        Logged when user sees a specific author by clicking on the link at author's name
    """
    author = models.ForeignKey(Author)
    
class AuthorHistory(abstract_models.AbstractUserHistory):
    """
        When user visits a paper, all authors in that paper will be logged
    """
    author = models.ForeignKey(Author)

class CategoryFocusHistory(abstract_models.AbstractUserHistory):
    """
        Logged when user sees a specific category by clicking on the link at category's name
    """
    category = models.ForeignKey(Category)

class CategoryHistory(abstract_models.AbstractUserHistory):
    """
        When user visits a paper, all categories in that paper will be logged
    """
    category = models.ForeignKey(Category)

class SearchHistory(abstract_models.AbstractUserHistory):
    """
        When user searches for a term, it is logged in this
    """
    search_term = models.CharField(max_length = 500)

class FullPaperViewHistory(abstract_models.AbstractUserHistory):
    """
        When user clicks on a link to view full paper content (e.g. pdf link)
    """
    paper = models.ForeignKey(Paper)

