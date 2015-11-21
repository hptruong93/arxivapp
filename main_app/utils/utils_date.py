from datetime import datetime

def string_to_date(string):
    try:
        return datetime.strptime(string, '%d/%m/%Y')
    except:
        return None