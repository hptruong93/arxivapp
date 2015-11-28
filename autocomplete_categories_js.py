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
from main_app import models as main_app_models

def do_generate():
	strings = []
	for category in main_app_models.Category.objects.all():
		strings.append(category.code)

	strings = map(lambda x : '"%s"' % x, strings)
	print ', '.join(strings)

if __name__ == "__main__":
	do_generate()	