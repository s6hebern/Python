# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 12:19:35 2014

@author: Hendrik
"""

### module for creating a "progess bar" ###
""" Generates a numerical progress bar of five-percent-steps. Arguments given \
to function progress(): iterator, which is the iterator within a loop, and \
iterable, which is the iterable object to which the loop is applied. """

def progress(iterator, iterable):

    percent = range(5, 105, 5)
    if len(iterable) == 0:
        print 'Iterable object has length 0!',
    else:
        if iterator == iterable[0]:
            print 'Progress (%): ' ,
        else:
            for i in percent:
                if iterator == round((len(iterable) - 1) * i / 100):
                    if i % 10 == 5:
                        print '.' ,
                    else:
                        print i ,
            if iterator == iterable[-1]:
                print '\n', 'Done!'
