#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
date: Fri Mar  4 12:59:37 2016
user: hendrik
"""

import sys

def progress(iterator, iterable):

    """ 
    Generates a numerical progress bar of five-percent-steps. Function has to be 
    called within the loop. 
    
    Use:
    
    iterator: the iterator of the loop.
    
    iterable: the iterable object to which the loop is applied.
    
    Example:
        for i in range(100):
            progress(i, range(100))
    """

    iterator = list(iterable).index(iterator)
    iterable = xrange(len(iterable))
    
    percent = range(5, 105, 5)
    if len(iterable) == 0:
        sys.stdout.write('Iterable object has length 0!')
    else:
        if iterator == iterable[0]:
            sys.stdout.write('Progress (%): ' ,)
        else:
            for i in percent:
                if iterator == round((len(iterable) - 1) * i / 100):
                    if i % 10 == 5:
                        sys.stdout.write( '. ' ,)
                    else:
                        sys.stdout.write(str(i) + ' ',)
            if iterator == iterable[-1]:
                sys.stdout.write('\n',)
