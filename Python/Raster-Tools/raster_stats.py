# -*- coding: utf-8 -*-

from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np

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
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, num_bands, \
                band.DataType)
    else:
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, num_bands, \
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
