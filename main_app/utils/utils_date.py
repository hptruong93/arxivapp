import datetime

DEFAULT_DATE_FORMAT = '%d/%m/%Y'
KNOWN_DATE_FORMATS = [DEFAULT_DATE_FORMAT, '%d-%b-%Y', '%Y-%b-%d', '%b-%d-%Y', '%Y/%m/%d', '%m/%d/%Y']

def string_to_date(string):
    for date_format in KNOWN_DATE_FORMATS:
        try:
            return datetime.datetime.strptime(string, date_format)
        except:
            pass
    return None

def date_to_string(date, date_format = DEFAULT_DATE_FORMAT):
    return date.strftime(date_format)

def previous_business_date(date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0), count_back = 1):
    delta = datetime.timedelta(days = 1)
    count_down = count_back
    while count_down > 0:
        new_date = date - delta

        if new_date.weekday() >= 5: #If Saturday or Sunday
            date = new_date
            continue

        count_down -= 1
        if count_down == 0:
            return new_date

    return date

def get_today():
    time_now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hour_now = time_now.hour

    if time_now.weekday() > 4:
        while time_now.weekday() > 4:
            time_now -= datetime.timedelta(days = 1)
        return time_now


    if hour_now < 22:
        return previous_business_date(count_back = 0)
    else:
        time_now = time_now.replace(hour=0, minute=0, second=0, microsecond=0)
        time_now += datetime.timedelta(days = 1)
        return time_now