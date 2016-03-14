#Author: HP Truong (phuoc.truong2@mail.mcgill.ca)
#This MUST be run in the same directory where manage.py file (django project) is
#Usage: python csv_extract.py absolute_path_to_csv_file

import os
import sys
import csv
import re
import traceback
import argparse
from datetime import datetime

#Setting up environment variable for django to work
os.environ['DJANGO_SETTINGS_MODULE'] = 'arxivapp.settings'

#Importing models from django project
from django.db import transaction
from main_app import models as main_app_models

DATE_FORMAT = '%Y-%m-%d'

def _parse_date(string):
    """
        Parse date from csv to python native datetime object.
        Arg: string is the string in format yyyy-mm-dd
        Return a python datetime object, or None if input string is empty
    """
    if len(string) > 0:
        return datetime.strptime(string.strip(), DATE_FORMAT)
    return None

def _date_to_str(date):
    return date.strftime(DATE_FORMAT)

def _import_author(full_name):
    """
        Attempt to import author into database
        Arg: full_name is the full name of the author (first middle last name)
        For now, treating the last word as the last name, and everything else as first name (i.e. no middle name)

        Return the django model object (either newly created, or fetched from database if already existed)
    """
    full_name = full_name.strip()
    if len(full_name) < 2:
        return None

    split = full_name.split(' ')
    first_name = ' '.join(split[:-1])
    last_name = split[-1]

    not_ends_with = ['jr', 'jr.', 'sr', 'sr.']
    is_good = True
    for string in not_ends_with:
        if last_name.lower().endswith(string):
            is_good = False

    if not is_good:
        last_name = split[-2] + ' ' + split[-1]
        first_name = ' '.join(split[:-2])

    print "Full name is %s while first and last are %s - %s" % (full_name, first_name, last_name)
    assert len(last_name) != 0

    author, is_new = main_app_models.Author.objects.get_or_create(first_name = first_name, last_name = last_name)
    
    return author

def _import_category(code):
    """
        Attempt to import a new category into database
        Arg: category code: arxiv code of the category (e.g. physics.class-ph)
        Arg: name: human readable name of the category

        Return the django model object (either newly created, or fetched from database if already existed)
    """
    category, is_new = main_app_models.Category.objects.get_or_create(code = code.strip())

    return category


def single_import(paper):
    arxiv_id = paper['id']
    categories = paper['categories'].split(' ')
    if len(categories) == 0:
        print "Papper {0} has no category?".format(arxiv_id)
        return

    try:
        inserting_paper = main_app_models.Paper.objects.get(arxiv_id = arxiv_id)
        primary_category_id = categories[0].strip()

        primary_category = main_app_models.Category.objects.get(code = primary_category_id.strip())
        inserting_paper.primary_category = primary_category

        inserting_paper.save()
    except main_app_models.Paper.DoesNotExist:
        print "Not found paper with id {0}".format(arxiv_id)
        return
    except main_app_models.Category.DoesNotExist:
        print "Not found category with id {0}".format(primary_category_id)
        return
    except Exception as e:
        print '------------------------------------------------------------------------'
        print inserting_paper
        print traceback.format_exc()
        sys.exit(1)



def import_data(filename, skip, bulk_size):
    """
        Import papers from a csv file
        Arg: filename: name of the input csv file
    """
    metadata = []
    transaction.set_autocommit(False)

    count_to_commit = bulk_size

    with open(filename, "rb") as csvfile:
        datareader = csv.reader(csvfile)
        count = -1

        for row in datareader:
            committed = False
            count += 1
            if count == 0:
                metadata = row
                continue

            if count <= skip:
                continue

            new_entry = {header : row[i].strip() for i, header in enumerate(metadata)}

            single_import(new_entry)
            count_to_commit -= 1
            if count_to_commit == 0:
                count_to_commit = bulk_size
                transaction.commit()

            # print "Count is %d" % count

    transaction.commit()
    transaction.set_autocommit(True)
    print "Done with file %s" % filename
            
if __name__ == "__main__":
    print "Assume this runs every day between 9pm and 10pm, and finishes before midnight"
    parser = argparse.ArgumentParser(description = 'Import data from a csv file')
    parser.add_argument('file_path', action = "store", help='Name of the csv file to import data from', type = str)
    parser.add_argument('-s', '--skip', dest='skip', default=0, help='Skip the first n lines in the data file', type = int)
    parser.add_argument('-b', '--bulk-size', dest='bulk_size', default=100, help='Import in bulk of this size. Default to 100', type = int)

    args = parser.parse_args()

    import_data(args.file_path, args.skip, args.bulk_size)
