# -*- coding: utf-8 -*-

# low-pass filter using pixel notation

import os, sys, time, datetime, gdal, string
import numpy as np
from gdalconst import *
from optparse import OptionParser, OptionGroup

__version__ = 1.0

# lowpass-filter for integer images
def lowpass_filter(img_in, img_out, window, mode='mean', band=1, of='GTiff', co=None):
    """
    Apply a lowpass filter to an (integer) image.


    Use:

    img_in (string): Input image (full path and file extension). May contain
            multiple bands.

    img_out (string): the output image (full path and file extension).

    window (integer): the size of the filter window. 3 means a filter size of
            3x3, 5 means 5x5, etc.
            IMPORTANT NOTE: the output image will be smaller than the input
                image! With a 3x3 filter, 1 pixel will be lost at EACH edge,
                with a 5x5 filter, 2 pixels, etc.

    mode (string): statistic to be used for filtering. One of:
            - "mean"
            - "median"
            - "min"
            - "max"
            NAs are omitted in any case.

    band (integer): the desired band of the input image which shall be filtered.
            Counting starts at 1 (default).

    of (string): the desired format of the output file as provided by the
            GDAL raster formats (see: http://www.gdal.org/formats_list.html).
            Defaults to 'GTiFF'.

    co (list): a list of strings, containing advanced raster creation
            options such as band interleave.

            Example:
                co=['interleave=bil','tiled=yes']
    """

    # set up input correctly
    window = int(window)
    band = int(band)

    # register all of the GDAL drivers
    gdal.AllRegister()

    # open the image
    print 'Reading input image...'
    inDs = gdal.Open(img_in, GA_ReadOnly)
    if inDs is None:
      print 'Could not open %s' %img_in
      sys.exit(1)

    # get image size
    rows = inDs.RasterYSize
    cols = inDs.RasterXSize

    # read the input data
    inBand = inDs.GetRasterBand(band)
    inData = inBand.ReadAsArray(0, 0, cols, rows).astype(np.int)

    # initiate output array
    outData = np.zeros((rows, cols), np.int)

    # do the calculation with array slices:
    rev = list(reversed(range(window)))
    # exp = '('
    exp = string.join(['np.nan', mode, '(['], sep='')

    # set up string command, that will later be evaluated
    for i in range(window):
        for j in rev:
            exp = string.join(
                [exp, 'inData[', str(i), ':rows-', str(rev[i]), ', ', str(rev[j]), \
                 ':cols-', str(j), '], '], sep='')

    exp = string.join([exp[:-2], '], axis=0)'], sep='')

    # evaluate string expression and fill outData with it
    print 'Filtering image %s with a %sx%s &s window...' %(os.path.basename(img_in), window, window, mode)
    outData[(window/2):rows-(window/2), (window/2):cols-(window/2)] = eval(exp)

    # for a window of 3x3 for a filter, exp would look like this:
    # outData[1:rows-1,1:cols-1] = np.nanmean(inData[0:rows-2, 0:cols-2] + \
    #                                           inData[0:rows-2, 1:cols-1] + \
    #                                           inData[0:rows-2, 2:cols-0] + \
    #                                           inData[1:rows-1, 0:cols-2] + \
    #                                           inData[1:rows-1, 1:cols-1] + \
    #                                           inData[1:rows-1, 2:cols-0] + \
    #                                           inData[2:rows-0, 0:cols-2] + \
    #                                           inData[2:rows-0, 1:cols-1] + \
    #                                           inData[2:rows-0, 2:cols-0])

    # create the output image
    print 'Creating output image %s' %img_out
    driver = gdal.GetDriverByName(of)
    if co == None:
        outDs = driver.Create(img_out, cols, rows, 1, inBand.DataType)
    else:
        outDs = driver.Create(img_out, cols, rows, 1, inBand.DataType, co)
    if outDs is None:
      print 'Could not create &s' %img_out
      sys.exit(1)

    outBand = outDs.GetRasterBand(1)

    # write the output data
    outBand.WriteArray(outData, 0, 0)

    # flush data to disk, set the NoData value and calculate stats
    outBand.FlushCache()
    stats = outBand.GetStatistics(0, 1)

    # georeference the image and set the projection
    outDs.SetGeoTransform(inDs.GetGeoTransform())
    outDs.SetProjection(inDs.GetProjection())

    inDs = None
    outDs = None


# run
def run():
    # create parser
    parser = OptionParser('%prog -i <input_image> -o <output_image> -w <window_size>', version='%prog 1.0')
    parser.add_option('-i', '--input_image', dest='img_in', help='<file> Input image')
    parser.add_option('-o', '--output_image', dest='img_out', help='<file> Output image')
    parser.add_option('-w', '--window_size', dest='win', help='<integer> Integer value for the filter size (3 => 3x3)')

    group = OptionGroup(parser, 'Optional Arguments', '')
    group.add_option('-m', '--mode', dest='mode', default='mean', help='<string> The desired statistical mode for the filter. One of: \n - "mean" \n - "median" \n - "min" \n -"max". NAs are omitted in any case.')
    group.add_option('-b', '--band', dest='band', default=1, help='<integer> The desired band of the input image which shall be filtered')
    group.add_option('-f', '--out_format', dest='of', default='GTiff', help='<string> File format of output image')
    group.add_option('-c', '--create_options', dest='co', help='<sequence of strings> Advanced raster creation options, such as band interleave. Example: -c "num_threads=all_cpus","tiled=yes"')
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    # mandatory options
    img = options.img_in
    out = options.img_out
    win = options.win
    # optional options
    mode = options.mode
    band = options.band
    of = options.of
    try:
        co = options.co.split(',')
    except:
        co = options.co

    # sort options to be able to parse them correctly even when user input is mixed up
    opts = [img, out, win, mode, band, of, co]
    index = 0
    for o in range(0,len(opts)):
        # find options not provided with their keyword
        if opts[o] == None:
            try:
                # assign option from list of arguments
                opts[o] = args[index]
                index += 1
            except:
                break
    # check user input
    if None in opts[0:2]:
        parser.error('Not all mandatory arguments have been provided! Please check your input and try again.')
        print parser.usage
        exit(0)
    else:
        print 'Executing %s ...' % __file__
        lowpass_filter(opts[0], opts[1], opts[2], opts[3], opts[4], opts[5], opts[6])
        print 'Done!'

# execute
if __name__ == '__main__':
    start = time.time()
    run()
print '\nDuration (hh:mm:ss): %s' %(datetime.timedelta(seconds=time.time() - start))
