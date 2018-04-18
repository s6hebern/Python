# -*- coding: utf-8 -*-

import os
import datetime
import string
from dateutil.relativedelta import relativedelta

def doy2date(year, doy, asType='date', sep='-'):
    """
    Convert year and day-of-year to date

    :param int year: year
    :param int doy: numbered day of the year (counting starts at 1)
    :param str sep: Year-Month-Day separator for output string
    :return: Date, either as datetime-format (default) or string with the given separator for Year-Month-Day
    """

    date = datetime.datetime.strptime(str(year) + str(doy), '%Y%j')
    if asType == 'str':
        year = str(date.year)
        month = str(date.month)
        day = str(date.day)
        datestr = string.join([year, month, day], sep=sep)
        return datestr
    elif asType == 'date':
        return date

def date2doy(date, sep='-'):
    """
    Convert string of date to tuple of year and Day-of-Year

    :param str date:
    :param str sep:
    :return: tuple of year and Day-of-Year (year, doy)
    """

    year = int(date.split(sep)[0])
    month = int(date.split(sep)[1])
    day = int(date.split(sep)[2])
    doy = datetime.date(year, month, day).timetuple().tm_yday
    return year, doy


def dayRange(start, end):
    """
    Create a range of dates as datetime objects.

    :param start: datetime object of start date
    :param end: datetime object of end date
    :return: range of datetime objects with timedelta = 1 day
    :example:
    for single_date in self.dayRange(start, end):
        year = single_date.year \n
        month = single_date.month \n
        day = single_date.day
    """
    for n in range(int((end - start).days)):
        yield start + datetime.timedelta(days=n)

def monthRange(start, end):
    """
    Create a range of dates as datetime objects.

    :param start: datetime object of start date
    :param end: datetime object of end date
    :return: range of datetime objects with timedelta = 1 month
    :example:
    for single_date in self.monthRange(start, end):
        year = single_date.year \n
        month = single_date.month \n
    """
    current = start
    while current <= end:
        yield current
        current += relativedelta(months=1)

def datestring2date(datestring, date_format):
    """
    Convert dates stored as strings to datetime objects

    :param str datestring: date in string format
    :param str date_format: string formatting to indicate date format
    :return: datetime object
    :example: datestring2date('2017-12-06', '%Y-%m-%d')
    """
    date = datetime.datetime.strptime(datestring, date_format)
    return date

def date2datestring(date, date_format):
    """
    Convert dates stored as strings to datetime objects

    :param datetime date: date as datetime object
    :param str date_format: string formatting to indicate date format
    :return: date as string
    :example: date2datestring(datetime.datetime.now(), '%Y-%m-%d')
    """
    datestring = datetime.datetime.strftime(date, date_format)
    return datestring
