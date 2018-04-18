# -*- coding: utf-8 -*-

import os, sys

def progressBar(iterator, iterable):
    """ 
    Generates a numerical progress bar of five-percent-steps. Function has to be 
    called within the loop. 

    :param iterator: the iterator of the loop.
    :param iterable: the iterable object to which the loop is applied.
    :return: nothing
    Example:\n
    for i in range(100):
        progressBar(i, range(100))
    """

    iterator = list(iterable).index(iterator)
    iterable = xrange(len(iterable))

    percent = range(5, 105, 5)
    if len(iterable) == 0:
        sys.stdout.write('Iterable object has length 0! Progress bar is disabled!')
    else:
        if iterator == iterable[0]:
            sys.stdout.write('Progress (%): 0 ', )
        else:
            for i in percent:
                if iterator == round((len(iterable) - 1) * i / 100):
                    if i % 10 == 5:
                        sys.stdout.write('. ', )
                    else:
                        sys.stdout.write(str(i) + ' ', )
            if iterator == iterable[-1]:
                sys.stdout.write('\nDone!\n', )

def progress(status, finish=False):
    """
    Self-updating progress indicator. Has to be called within loop.

    :param float status: Status in percent
    :param bool finish: Boolean indicator for end of iteration
    :return: nothing
    Example:\n
    for i in range(100):
        percent = float(i)/len(range(100))*100 \n
        if i != range(100)[-1]:
            progress(percent, False)
        else:
            progress(percent, True)
    """

    if finish:
        status = 100.0
    sys.stdout.write('\r\tProgress: %.2f %%' % status)
    if finish:
        sys.stdout.write('\n')
    sys.stdout.flush()
