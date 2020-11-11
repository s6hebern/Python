# -*- coding: utf-8 -*-

import time
import datetime
import string
from dateutil.relativedelta import relativedelta
from dateutil import tz


def dec_time_to_hms(duration, basis='h', outformat='%H:%M:%S'):
    # type: (float, str, str) -> str
    """
    Convert a duration (number) into a hh:mm:ss string representation

    :param duration: Time duration as a number (may also be int)
    :param basis: Unit in which 'duration' is given. Allowed values are: 'h', 'hours', 'm', 'minutes', 's', 'seconds'
    :param outformat: Desired time format. Default is '%H:%M:%S', e.g. 08:43:02
    :return: hh:mm:ss string representation
    """
    allowed_formats = ('h', 'hours', 'm', 'minutes', 's', 'seconds')
    basis = basis.lower()
    if basis not in allowed_formats:
        raise ValueError('Parameter "outformat" not given correctly! Must be one of {af}'.format(af=allowed_formats))
    if basis == 'h' or basis == 'hours':
        td = datetime.timedelta(hours=duration)
    elif basis == 'm' or basis == 'minutes':
        td = datetime.timedelta(minutes=duration)
    else:
        td = datetime.timedelta(seconds=duration)
    return time.strftime(outformat, time.gmtime(td.seconds))


def hms_to_dec_time(hours, minutes, seconds, outformat='h'):
    # type: (int, int, int or float, str) -> float
    """
    Convert hours, minutes, seconds to decimal representation

    :param hours: Hours
    :param minutes: Minutes
    :param seconds: Seconds (may also be int)
    :param outformat: Desired decimal basis. Allowed values are: 'h', 'hours', 'm', 'minutes', 's', 'seconds'
    :return: Decimal representation of the given time
    """
    allowed_formats = ('h', 'hours', 'm', 'minutes', 's', 'seconds')
    outformat = outformat.lower()
    if outformat not in allowed_formats:
        raise ValueError('Parameter "outformat" not given correctly! Must be one of {af}'.format(af=allowed_formats))
    td = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if outformat == 'h' or outformat == 'hours':
        return float(td.seconds) / 60 / 60
    elif outformat == 'm' or outformat == 'minutes':
        return float(td.seconds) / 60
    else:
        return float(td.seconds)


def local_to_utc(local_dt, timezone=None):
    # type: (datetime.datetime, str) -> datetime.datetime
    """
    Convert local time to UTC

    :param datetime local_dt: Local time
    :param str timezone: Local timezone (None for auto detection). Check
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for valid options.
    :return: Time in local timezone
    """
    utc_zone = tz.gettz('UTC')
    if timezone:
        try:
            local_zone = tz.gettz(timezone)
        except:
            print('Invalid timezone indication! Using auto-detection instead!')
            local_zone = tz.tzlocal()
    else:
        local_zone = tz.tzlocal()
    local_dt = local_dt.replace(tzinfo=local_zone)
    print('Converting {z} to UTC'.format(z=local_zone._filename))
    return local_dt.astimezone(utc_zone)


def utc_to_local(utc_dt, timezone=None):
    # type: (datetime.datetime, str) -> datetime.datetime
    """
    Convert UTC time to local time

    :param utc_dt:
    :param timezone: local timezone (None for auto detection). Check
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for valid options.
    :return: Time in local timezone
    """
    utc_zone = tz.gettz('UTC')
    if timezone:
        try:
            local_zone = tz.gettz(timezone)
        except:
            print('Invalid timezone indication! Using auto-detection instead!')
            local_zone = tz.tzlocal()
    else:
        local_zone = tz.tzlocal()
    utc_dt = utc_dt.replace(tzinfo=utc_zone)
    print('Converting from UTC to {z}'.format(z=local_zone._filename))
    return utc_dt.astimezone(local_zone)


def doy_to_date(year, doy, as_type='date', sep='-'):
    # type: (int, int, str, str) -> datetime.datetime or str
    """
    Convert year and day-of-year to date

    :param year: year
    :param doy: numbered day of the year (counting starts at 1)
    :param as_type: desired output format for date (either "str" or "date")
    :param sep: Year-Month-Day separator for output string
    :return: Date, either as datetime-format (default) or string with the given separator for
            Year-Month-Day
    """
    date = datetime.datetime.strptime(str(year) + str(doy), '%Y%j')
    if as_type.lower() == 'str':
        year = str(date.year)
        month = str(date.month)
        day = str(date.day)
        datestr = string.join([year, month, day], sep=sep)
        return datestr
    elif as_type.lower() == 'date':
        return date
    else:
        raise ValueError('Wrong value for "asType". Has to be either "str" or "date"!')


def date_to_doy(date, sep='-'):
    # type: (str, str) -> (int, int)
    """
    Convert string of date to tuple of year and Day-of-Year

    :param date: Date as string
    :param sep: Separator for Year-Month-Day
    :return: tuple of year and Day-of-Year (year, doy)
    """
    year = int(date.split(sep)[0])
    month = int(date.split(sep)[1])
    day = int(date.split(sep)[2])
    doy = datetime.date(year, month, day).timetuple().tm_yday
    return year, doy


def day_range(start, end):
    # type: (datetime.datetime, datetime.datetime) -> datetime.datetime
    """
    Generator for a range of dates (days) as datetime objects.

    Example:\n
    for single_date in self.dayRange(start, end):
        year = single_date.year \n
        month = single_date.month \n
        day = single_date.day

    :param start: start date
    :param end: end date
    :return: range of datetime objects with timedelta = 1 day
    """
    for n in range(int((end - start).days)):
        yield start + datetime.timedelta(days=n)


def month_range(start, end):
    # type: (datetime.datetime, datetime.datetime) -> datetime.datetime
    """
    Generator for a range of dates (months) as datetime objects.

    Example:\n
    for single_date in self.monthRange(start, end):
        year = single_date.year \n
        month = single_date.month \n

    :param datetime start: start date
    :param datetime end: end date
    :return: range of datetime objects with timedelta = 1 month
    :rtype: range
    """
    current = start
    while current <= end:
        yield current
        current += relativedelta(months=1)


if __name__ == '__main__':
    print(doy_to_date(2015, 186))
    print(doy_to_date(2017, 105))
    print(hms_to_dec_time(12, 04, 43.175, 'h'))
    print(dec_time_to_hms(12.0786111111, basis='h'))
