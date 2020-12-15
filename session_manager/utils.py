from datetime import datetime, timedelta
import pytz


class TimeDiff(object):
    """ Helper class for getting quick time diffs used
        throughout session manager apps
    """

    @classmethod
    def twentyfourhoursfromnow(cls):
        """ Helper function for getting datetime 1 day from now
        """
        utc=pytz.UTC
        return utc.localize(datetime.now()) + timedelta(1)

    @classmethod
    def fourtyeighthoursfromnow(cls):
        """ Helper function for getting datetime 1 day from now
        """
        utc=pytz.UTC
        return utc.localize(datetime.now()) + timedelta(1)

    @classmethod
    def oneweekfromnow(cls):
        """ Helper function for getting datetime 1 week from now
        """
        utc=pytz.UTC
        return utc.localize(datetime.now()) + timedelta(7)

    @classmethod
    def yesterday(cls):
        """ Helper function for getting datetime from yesterday
        """
        utc=pytz.UTC
        return utc.localize(datetime.now()) + timedelta(-1)


special_chars = [
    '!',
    '@',
    '#',
    '$',
    '%',
    '^',
    '&',
    '*',
    '(',
    ')',
    '~',
    ';',
    ':',
    '<',
    '>',
    '"',
    '?',
    '/',
    "'",
    '[',
    ']',
    '|',
    '\\'
    '-',
    '_',
    '{',
    '}',
]
