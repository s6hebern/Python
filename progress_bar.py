# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 12:19:35 2014

@author: Hendrik
"""

### module for creating a "progess bar" ###
""" Generates a numerical progress bar of five-percent-steps. Arguments given \
to function progress(): iterator, which is the iterator within a loop, and \
iterable, which is the iterable object to which the loop is applied. """

class prog_Bar():
    def __init__(self, parent = None):
        self.percent = range(5, 105, 5)
        print 'Progress (%): ' ,
        
    def progress(self, iterator, iterable):
        for i in self.percent:
            if iterator == round((len(iterable) - 1) * i / 100):
                if i % 10 == 5:
                    print '.' ,
                else:
                    print i ,
        print '\n'
