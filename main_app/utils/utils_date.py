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
    return date.strftime(date_format) if date else date

def previous_business_date(date = None, count_back = 1):
    if date is None:
        date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

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
    time_now = datetime.datetime.now()
    hour_now = time_now.hour
    time_now = time_now.replace(hour=0, minute=0, second=0, microsecond=0)

    #If weekend (i.e. Sat or Sun)
    if time_now.weekday() > 4:
        while time_now.weekday() > 4:
            time_now -= datetime.timedelta(days = 1)
        return time_now


    #The daily paper import finishes at 2AM UTC of that day. Therefore,
    #if hour < 2AM then we have to show the previous date.
    #There could be a minor difference if daylight saving is present, but it does not
    #really affect result that much (user may have incorrect result for one hour at most).
    if hour_now < 2:
        time_now = time_now.replace(hour=0, minute=0, second=0, microsecond=0)
        return previous_business_date(time_now, count_back = 1)
    else: #Otherwise, we show paper of the current date
        return previous_business_date(count_back = 0)