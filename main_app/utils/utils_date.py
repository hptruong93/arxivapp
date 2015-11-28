from datetime import datetime

DEFAULT_DATE_FORMAT = '%d/%m/%Y'
KNOWN_DATE_FORMATS = [DEFAULT_DATE_FORMAT, '%d-%b-%Y', '%Y-%b-%d', '%b-%d-%Y', '%Y/%m/%d', '%m/%d/%Y']

def string_to_date(string):
	for date_format in KNOWN_DATE_FORMATS:
	    try:
	        return datetime.strptime(string, date_format)
	    except:
	        pass
	return None

def date_to_string(date, date_format = DEFAULT_DATE_FORMAT):
	return date.strftime(date_format)