import traceback
import os

#Setting up environment variable for django to work
os.environ['DJANGO_SETTINGS_MODULE'] = 'arxivapp.settings'

#Importing models from django project
from main_app import models as main_app_models

if __name__ == "__main__":
    with open('subject_classifications', 'r') as f:
        for line in f:
            line = line.strip().split('\t')

            category_code = line[0]
            category_name = line[1]
            print "Importing category %s, %s" % (category_code, category_name)

            model, created = main_app_models.Category.objects.get_or_create(code = category_code)
            model.name = category_name
            model.save()

    print "Done importing categories"