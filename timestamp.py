import datetime


def timestamp():
    return datetime.datetime.now().strftime("[%m/%d | %H:%M]")