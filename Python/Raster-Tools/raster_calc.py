# -*- coding: utf-8 -*-

import os, sys, time, datetime
from optparse import OptionParser, OptionGroup

from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np

__version__ = 1.0

def raster_calc(img_a, img_b, mode, outfile, band_a=None, band_b=None, of='GTiff', co=None):
    
    """
    Combine two rasters based on one of the four basic arithmetic operations.
    
    
    Use:
    
    a (string): first input image (full path and file extension). May contain 
            multiple bands.
    
    b (string): second input image (full path and file extension). May contain 
            multiple bands.
    
    mode (string): the arithmetic operation. Must be one of:
            - 'add'
            - 'subtract'
            - 'multiply'
            - 'divide'

    outfile (string): the output image (full path and file extension).
    
    band_a (integer): the desired band of the first input image which shall be
            used for the calculation, if it is a multiband image.
    
    band_b (integer): the desired band of the second input image which shall be
            used for the calculation, if it is a multiband image.
    
    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
    
    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.
            
            Example:
                co=['interleave=bil','tiled=yes']
    """    


    gdal.AllRegister()
    driver = gdal.GetDriverByName(of)

    # read data:    
    ds_a = gdal.Open(img_a, GA_ReadOnly)
    ds_b = gdal.Open(img_b, GA_ReadOnly)

    if band_a != None:
        b_a = ds_a.GetRasterBand(band_a)
    else:
        b_a = ds_a.GetRasterBand(1)
    
    if band_b != None:
        b_b = ds_b.GetRasterBand(band_b)
    else:
        b_b = ds_b.GetRasterBand(1)
        
    data_a = b_a.ReadAsArray()
    data_b = b_b.ReadAsArray()
    
    # create output file:
    if co == None:
        ds_out = driver.Create(outfile, ds_a.RasterXSize, ds_a.RasterYSize, 1, \
                b_a.DataType)
    else:
        ds_out = driver.Create(outfile, ds_a.RasterXSize, ds_a.RasterYSize, 1, \
                b_a.DataType, co)
    ds_out.SetProjection(ds_a.GetProjection())
    ds_out.SetGeoTransform(ds_a.GetGeoTransform())
    
    if mode == 'add':
        data_out = np.add(data_a, data_b)
    elif mode == 'subtract':
        data_out = np.subtract(data_a, data_b)
    elif mode == 'multiply':
        data_out = np.multiply(data_a, data_b)
    elif mode == 'divide':
        data_out = np.divide(data_a, data_b)
    else:
        raise ValueError('Error: mode must be one of "add", "subtract", "multiply" or "divide"!')
    
    b_out = ds_out.GetRasterBand(1)
    b_out.WriteArray(data_out)
    
    b_out = None
    ds_out = None
    ds_b = None
    ds_a = None

def run():
    # create parser
    parser = OptionParser('%prog -a <image_a> -b <image_b> -m <mode> -o <outfile> [options]', version='%prog 1.0')
    parser.add_option('-a', '--image_a', dest='img_a', help='<file> First input image')
    parser.add_option('-b', '--image_b', dest='img_b', help='<file> Second input image')
    parser.add_option('-m', '--mode', dest='mode', help='<string> Arithmetic operation to run (one of "add", "subtract", "multiply", "divide"')
    parser.add_option('-o', '--output', dest='outfile', help='<file> Output image')
    group = OptionGroup(parser, 'Optional Arguments', '')
    group.add_option('-x', '--band_a', dest='band_a', default=1, help='<integer> The desired band of the first input image which shall be used for the calculation, if it is a multiband image')
    group.add_option('-y', '--band_b', dest='band_b', default=1, help='<integer> The desired band of the second input image which shall be used for the calculation, if it is a multiband image')
    group.add_option('-f', '--out_format', dest='of', default='GTiff', help='<string> File format of output image')
    group.add_option('-c', '--create_options', dest='co', help='<sequence of strings> Advanced raster creation options, such as band interleave. Example: -c "num_threads=all_cpus","tiled=yes"')
    parser.add_option_group(group)
    
    (options, args) = parser.parse_args()

    # mandatory options    
    a = options.img_a
    b = options.img_b
    mode = options.mode
    outfile = options.outfile
    # optional options
    band_a = options.band_a
    band_b = options.band_b
    of = options.of
    co = options.co.split(',')
    # sort options to be able to parse them correctly even when user input is mixed up
    opts = [a, b, mode, outfile, band_a, band_b, of, co]
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
    if None in opts[0:4]:
        parser.error('Not all mandatory arguments have been provided! Please check your input and try again.')
        print parser.usage
        exit(0)
    else:
        print 'Executing %s ...' % __file__
        if str(mode) == 'add':
            print 'Summing up \n %s - band %s - \n and \n %s - band % s -' %(os.path.basename(a), band_a, os.path.basename(b), band_b)
        elif str(mode) == 'subtract':
            print 'Subtracting \n %s - band %s - \n from \n %s - band % s -' %(os.path.basename(b), band_b, os.path.basename(a), band_a)
        elif str(mode) == 'multiply':
            print 'Multiplying \n %s - band %s - \n and \n %s - band % s -' %(os.path.basename(a), band_a, os.path.basename(b), band_b)
        elif str(mode) == 'divide':
            print 'Dividing \n %s - band %s - \n by \n %s - band % s -'  %(os.path.basename(a), band_a, os.path.basename(b), band_b)
        raster_calc(opts[0], opts[1], opts[2], opts[3], opts[4], opts[5], opts[6], opts[7])
        print 'Done!'

# execute
if __name__ == '__main__':
    start = time.time()
    run()
    print 'Duration (hh:mm:ss): \n %s' %(datetime.timedelta(seconds=time.time() - start))
