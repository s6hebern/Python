# -*- coding: utf-8 -*-

""" 
    Generates a numerical progress bar of five-percent-steps. Function has to be 
    called within the loop. 
    
    Use:
    
    iterator: the iterator of the loop.
    
    iterable: the iterable object to which the loop is applied.
"""

def progress(iterator, iterable):
    iterator = iterable.index(iterator)
    iterable = xrange(len(iterable))
    
    percent = range(5, 105, 5)
    if len(iterable) == 0:
        print 'Iterable object has length 0!'
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
                print '\n',
