# -*- coding: utf-8 -*-

import os, datetime, string

def doy2date(doy):
    """
    Convert string with year and day of year to date

    :param string doy: e.g. '2018076'
    :return: date as string, e.g. 20180317
    """
    date = datetime.datetime.strptime(doy, '%Y%j')
    year = str(date.year)
    month = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    date_str = string.join([year, month, day], sep='')
    print 'DOY: %s   -->   Date: %s' %(doy, date_str)
    return date_str

def date2doy(date):
    """
    Convert string of date to day of year

    :param string date: date as string, e.g. 20180317
    :return: day of year as string, e.g. 2018076
    """
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    doy = str(datetime.date(year, month, day).timetuple().tm_yday)
    doy_str = string.join([year, doy.zfill(3)], sep='')
    print 'Date: %s   -->   DOY: %s' %(date, doy_str)
    return doy_str

def namedDate2doy(date):
    """
    Convert a date, given with its month by name, to day of the year

    :param string date: e.g. 'Mar 17 2018'
    :return: day of year as string, e.g. 2018076
    """
    date = datetime.datetime.strptime(date, '%b %d %Y')
    doy = date.timetuple().tm_yday
    doy_str = string.join([year, doy.zfill(3)], sep='')
    print 'Date: %s   -->   DOY: %s' %(date, doy_str)
    return doy_str
