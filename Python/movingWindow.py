import string
import numpy as np


def movingWindow(array, window, fun, args):
    """
    Apply a function using a moving window. The array will be expanded by duplicating the outer pixels, so the output
    array will have the same size as the input array.

    :param array array: Input array (must be 2D)
    :param int window: window size for array slices. Must be odd!
    :param str fun: Function to apply, e.g. 'numpy.nanmean'
    :param str args: additional arguments to be passed to function, e.g. axis=0
    :return: array
    :rtype: array
    :example:
    image = np.array([[0, 0, 1, 1, 1, 0],
                        [0, 0, 1, 1, 2, 3], \n
                        [0, 2, 2, 2, 4, 1], \n
                        [2, 2, 3, 3, 0, 0], \n
                        [1, 2, 2, 0, 0, 4], \n
                        [1, 2, 0, 0, 0, 3]], dtype=np.uint8)
    out = movingWindow(image, 2, 'np.nanmean', 'axis=0')
    """

    if window % 2 == 0:
        raise ValueError('Window size must be odd!')
    rows = array.shape[0]
    cols = array.shape[1]
    rev = list(reversed(range(window)))
    # duplicate outer pixels to expand image, so the output will have the same size as the input
    inData = array
    for n in range(window/2):
        inData = np.insert(inData, 0, inData[:, 0], axis=1) # left
        inData = np.insert(inData, -1, inData[:, -1], axis=1) # right
        inData = np.insert(inData, 0, inData[0, :], axis=0)  # top
        inData = np.insert(inData, -1, inData[-1, :], axis=0)  # bottom
    exp = string.join([fun, '(['], sep='')
    for i in range(window):
        for j in rev:
            exp = string.join(
                [exp, 'inData[', str(i), ':rows-', str(rev[i]), ', ', str(rev[j]), ':cols-', str(j), '], '], sep='')
    exp = string.join([exp[:-2], '], {args})'.format(args=args)], sep='')
    # ----------------------------------------------------------------------- #
    # for a window of 3x3 for a filter, exp would look like this:
    # outData[1:rows-1,1:cols-1] = np.nanmean(inData[0:rows-2, 0:cols-2] + \
    #                                           inData[0:rows-2, 1:cols-1] + \
    #                                           inData[0:rows-2, 2:cols-0] + \
    #                                           inData[1:rows-1, 0:cols-2] + \
    #                                           inData[1:rows-1, 1:cols-1] + \
    #                                           inData[1:rows-1, 2:cols-0] + \
    #                                           inData[2:rows-0, 0:cols-2] + \
    #                                           inData[2:rows-0, 1:cols-1] + \
    #                                           inData[2:rows-0, 2:cols-0], \
    #                                           axis=0)
    # ----------------------------------------------------------------------- #
    # evaluate string expression and fill outData with it
    outData = np.zeros(array.shape, dtype=np.float32)
    outData[(window/2):rows - (window/2), (window/2):cols - (window/2)] = eval(exp)
    return outData


if __name__ == '__main__':
    image = np.array([[0, 0, 1, 1, 1, 0],
                      [0, 0, 1, 1, 2, 3],
                      [0, 2, 2, 2, 4, 1],
                      [2, 2, 3, 3, 0, 0],
                      [1, 2, 2, 0, 0, 4],
                      [1, 2, 0, 0, 0, 3]], dtype=np.uint8)
    out = movingWindow(image, 3, 'np.nanmean', 'axis=0')
    print image
    print out
