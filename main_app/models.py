from django.db import models
import abstract_models

# Create your models here.
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
    abstract = models.CharField(max_length=4000)
    link_full_text_pdf = models.CharField(max_length=700, null = True)

    def __unicode__(self):
        return self.title

class PaperHistory(abstract_models.AbstractUserHistory):
    paper = models.ForeignKey(Paper)
    
class AuthorHistory(abstract_models.AbstractUserHistory):
    author = models.ForeignKey(Author)

class CategoryHistory(abstract_models.AbstractUserHistory):
    category = models.ForeignKey(Category)
