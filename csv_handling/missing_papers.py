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

missing_papers = set()

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
    """
        Attempt to import a single paper entry into database
        Arg: paper: a dictionary with the following fields present:
                            id --> arxiv_id
                            created --> date created (nullable)
                            updated --> date updated (nullable)
                            title --> paper title
                            authors --> comma separated author full names 
                            (this method will ignore anything in single brackets e.g. Williams (Jr) will be interpreted as Williams)
                            categories --> comma separated category codes
                            journal-ref --> journal reference of the paper
                            abstract --> paper abstract

        This method will either create a new object representing the model in the database, or modify the exisiting object in database to match the
        input content
    """
    arxiv_id = paper['id']
    if arxiv_id not in missing_papers:
        return

    created_date = paper['created']
    created_date = _parse_date(created_date)

    updated_date = paper['updated']
    updated_date = _parse_date(updated_date)

    imported_date = paper['imported_date']
    imported_date = _parse_date(imported_date)

    title = paper['title']

    authors = paper['authors'].replace('\\,', '')

    authors = re.sub(r'\(.*?\)', '', authors).strip().split(', ')
    not_ends_with = ['jr', 'jr.', 'sr', 'sr.']
    for index, full_name in enumerate(authors):
        full_name = full_name.strip()

        is_good = True
        for string in not_ends_with:
            if full_name.lower().endswith(string):
                is_good = False
                break

        if not is_good:
            authors[index - 1] += ' ' + full_name
            authors[index] = ''

    # print "Authors are %s" % authors

    categories = paper['categories'].split(' ')
    journal_ref = paper['journal-ref']
    if len(journal_ref) == 0:
        journal_ref = None

    abstract = paper['abstract']

    inserting_paper, is_new = main_app_models.Paper.objects.get_or_create(arxiv_id = arxiv_id)
    inserting_paper.created_date = created_date
    inserting_paper.updated_date = updated_date
    inserting_paper.last_resigered_date = imported_date #See models.py for more information about this field
    inserting_paper.journal_ref = journal_ref
    inserting_paper.title = title
    inserting_paper.abstract = abstract

    imported_authors = map(_import_author, authors)
    imported_categories = map(_import_category, categories)

    for author in imported_authors:
        if author:
            inserting_paper.authors.add(author)

    for index, category in enumerate(imported_categories):
        #Assume first category to always be main category
        if index == 0:
            inserting_paper.primary_category = category
        inserting_paper.categories.add(category)

    try:
        inserting_paper.save()
    except Exception as e:
        print '------------------------------------------------------------------------'
        print inserting_paper
        print traceback.format_exc()
        sys.exit(1)



def import_data(filename, skip, bulk_size, imported_date):
    """
        Import papers from a csv file
        Arg: filename: name of the input csv file
    """
    if imported_date is None:
        imported_date = _date_to_str(datetime.now())

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
            new_entry['imported_date'] = imported_date

            single_import(new_entry)
            count_to_commit -= 1
            if count_to_commit == 0:
                count_to_commit = bulk_size
                transaction.commit()

            print "Count is %d" % count

    transaction.commit()
    transaction.set_autocommit(True)
    print "Done with file %s" % filename
            
if __name__ == "__main__":
    with open('result.txt', 'r') as f:
        for line in f:
            line = line.strip()
            current_paper = line.split(' ')[-1]
            missing_papers.add(current_paper)


    parser = argparse.ArgumentParser(description = 'Import data from a csv file')
    parser.add_argument('file_path', action = "store", help='Name of the csv file to import data from', type = str)
    parser.add_argument('-s', '--skip', dest='skip', default=0, help='Skip the first n lines in the data file', type = int)
    parser.add_argument('-b', '--bulk-size', dest='bulk_size', default=100, help='Import in bulk of this size. Default to 100', type = int)
    parser.add_argument('-d', '--date', dest='imported_date', default=None, help='Date on which the data is imported (yyyy-mm-dd). Default to be today', type = int)

    args = parser.parse_args()

    import_data(args.file_path, args.skip, args.bulk_size, args.imported_date)
