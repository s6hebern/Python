# -*- coding: utf-8 -*-

import os, sys
from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np
import csv

def calc_stat_raster(infile, outfile, mode, of="GTiff", co=None):
    
    """
    Create an image containing a basic statistical value from a multiband-image.
    
    
    Use:
    
    infile (string): the (multiband) input image (full path and file extension).
    
    outfile (string): the output image (full path and file extension).
    
    mode (string / list): the desired statistical value(s). If a string is
            given, the output image will contain one band with the specified 
            value. If a list of strings is given, one band will be created for 
            each list element (in the same order).
            
            mode can be chosen from the following numpy functions:
                    - mean
                    - median
                    - min
                    - max
                    - sum
                    - std
    
    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.

    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.
            
            Example:
                co=['interleave=bil']
    """

    gdal.AllRegister()
    driver = gdal.GetDriverByName(of)
    
    ds = gdal.Open(infile, GA_ReadOnly)
    band = ds.GetRasterBand(1)
    ds_arr = ds.ReadAsArray()
    
    # write outfile:
    if type(mode) == str:
        num_bands = 1
    else:
        num_bands = len(mode)
    
    if co == None:
        ds_out = driver.Create(outfile, ds.RasterXSize, ds.RasterYSize, num_bands, \
                band.DataType)
    else:
        ds_out = driver.Create(outfile, ds.RasterXSize, ds.RasterYSize, num_bands, \
                band.DataType, co)
    
    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())
    
    for b in xrange(1, num_bands + 1):
        b_out = ds_out.GetRasterBand(b)
        
        # calculate desired statistical value(s):
        if type(mode) == str:
            stat = getattr(np, mode)
        else:
            stat = getattr(np, mode[b - 1])

        data = stat(ds_arr, axis=0)
        # write data:
        b_out.WriteArray(data)
        # set band name to statistical value(s):
        if type(mode) == str:
            b_out.SetDescription(mode)
        else:
            b_out.SetDescription(mode[b - 1])
            
        b_out = None
    
    ds_out = None
    ds = None


def histogram(infile, band=1, outfile=None, delim=','):
    
    """
    Compute the exact histogram of an 8bit image, which can be written into a
    csv file containing all values and counts within the min-max-range.
    
    Use:
    
    infile (string): the input image (full path and file extension). May 
            contain multiple bands
    
    band (integer): the number of the image band from which the histogram shall
            be computed. Counting starts at 1. Defaults to 1.
    
    outfile (string): the output file (full path and file extension), if the
            histogram shall be written into a csv file. Defaults to None, which
            means that no output file is created. Nonetheless, the histogram 
            itself is returned.
    
    delim (string): the delimiter to use for the csv file. Defaults to ",".
    """
    
    b_index = band
    # read file:
    ds = gdal.Open(infile, GA_ReadOnly)
    band = ds.GetRasterBand(b_index)
    # get min/max and compute exact histogram:
    minmax = band.ComputeRasterMinMax()
    hist = band.GetHistogram(approx_ok=0)
    
    # write histogram to csv, if desired:
    if outfile != None:
        values = [i for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
        counts = [hist[i] for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
        # create csv
        with open(outfile, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=delim)
            writer.writerow(['Value', 'Count'])
            writer.writerows(zip(values, counts))
    # return histogram for further analysis:
    return(hist)


def area_per_class(infile, outfile, band=1, delim=','):
    
    """
    Compute the per-class-area from a classification image and create a csv 
            table from it.
    
    Use:
    
    infile (string): the input image (full path and file extension). May 
            contain multiple bands
    
    outfile (string): the output file (full path and file extension), if the
            histogram shall be written into a csv file. Defaults to None, which
            means that no output file is created. Nonetheless, the histogram 
            itself is returned.
    
    band (integer): the number of the image band from which the histogram shall
            be computed. Counting starts at 1. Defaults to 1.
            
    delim (string): the delimiter to use for the csv file. Defaults to ",".
    """
    
    b_index = band
    # read file:
    ds = gdal.Open(infile, GA_ReadOnly)
    band = ds.GetRasterBand(b_index)
    # get raster metrics:
    reso = ds.GetGeoTransform()[1]
    
    # get histogram (using function "histogram"):
    hist = histogram(infile, b_index)
    minmax = band.ComputeRasterMinMax()
    values = [i for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
    counts = [hist[i] for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
    
    # calculate area per class (apc):
    apc = [i * (reso * reso) for i in counts]
    
    # write csv:
    values = [i for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
    counts = [hist[i] for i in xrange(int(minmax[0]), int(minmax[1]) + 1)]
    # create csv
    with open(outfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=delim)
        writer.writerow(['Value', 'Count', 'Area'])
        writer.writerows(zip(values, counts, apc))
