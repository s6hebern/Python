# -*- coding: utf-8 -*-

import os
import sys
import string
from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np

def create_mask(image, values, valRange=True, dataBand=None, outName=None, \
        outPath=None, outFormat='GTiff', nodata=None):
    
    """
    Create a binary mask (containing only 0 and 1) from an image (which may 
            contain more than one band).
    
    Use:
    
    image (string): the image file (full path and file extension).
    
    values (list): a list containing the minimum (first entry) and maximum 
            (second entry) values of the data range which shall be set to 1. If
            only one entry is given, this value will be set to 1, all others to
            0.
            
    valRange (boolean): Defaults to 'True', which means that a range of two 
            values is given (minimum and maximum). If set to 'False', the exact
            values of the given list will be taken to set to 1.
            
    dataBand (integer): the band number of the desired band to use, if the input
            image contains more than one band.
            
    outName (string): the name of the output file (with file extension). 
            Defaults to the name of the input image, extended by '_mask'.
            
    outpath (string): the directory to which the output file will be written. 
            Defaults to the parent directory of the input image.
            
    outFormat (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
	
	nodata (integer): the desired NoData-value to be set.
    """
    
    gdal.AllRegister()
    driver = gdal.GetDriverByName(outFormat)
    
    ds = gdal.Open(image, GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    if dataBand == None:
        band =  ds.GetRasterBand(1)
    else:
        band = ds.GetRasterBand(dataBand)

    data = band.ReadAsArray(0, 0, cols, rows)
    # search for the desired values to be set to 1, set all others 0, making use
    # of the 'eval'-function to concatenate all desired values to a single 
    # 'or'.statement for numpy (if a list of values is given instead of a range):
    val_strings = []
    if valRange == True:
        mask = np.where(((data >= values[0]) & (data <= values[1])), 1, 0)
    else:
        for i in xrange(len(values)):
            val_strings.append(string.join(['(data == ', str(values[i]), ')'], sep=''))
        exp = 'np.where((' + string.join([v for v in val_strings], sep=' | ') + '), 1, 0)'
        mask = eval(exp)
    # clean RAM:
    data = None
    band = None
    # create output name:
    if outName == None:
        if outPath == None:
            outname = string.join([os.path.splitext(image)[0], '_mask', \
                                    os.path.splitext(image)[1]], sep='')
        else:
            outname = os.path.join(outPath, \
                            string.join([os.path.splitext(image)[0], '_mask', \
                                        os.path.splitext(image)[1]], sep=''))
    else:
        if outPath == None:
            outname = os.path.join(os.path.dirname(image), outName)
        else:
            outname = os.path.join(outPath, outName)
    # create output file (with GDAL data type 1 (Byte)):
    ds_out = driver.Create(outname, cols, rows, 1, 1)
    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())
    b_out = ds_out.GetRasterBand(1)
    b_out.WriteArray(mask)
    
    if nodata != None:
        b_out.SetNoDataValue(nodata)
    
    b_out = None
    ds_out = None
    ds = None
