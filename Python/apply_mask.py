# -*- coding: utf-8 -*-

import os
import sys
from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np
from scipy import misc

try:
    import module_progress_bar as pr
except:
    pass

def apply_mask(image, maskImage, outName, outPath=None, outFormat='Gtiff', \
        outExtent='image', interpolation='nearest'):

    """
    Apply a mask to a (multiband) image. The mask will be multiplied with the 
    input image. Both images have to cover the same area, but may differ in 
    resolution.
    
    Use:
    
    image (string): the image file (full path and file extension).
    
    maskImage (string): the image file which shall be used as mask (full path 
            and file extension).
    
    outName (string): the name of the output file (with file extension).
    
    outpath (string): the directory to which the output file will be written. 
            Defaults to the parent directory of the input image.
    
    outFormat (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
    
    outExtent (string): the desired extent and resolution of the output image,
            if input and mask image have different dimensions. 
            Possible values are:
                - 'image' (default)
                - 'mask'
    
    interpolation (string): the interpolation method to be used if input and 
            mask image have different dimensions. The image specified in 
            'outExtent' will then be resampled using this interpolation method.
            Possible values are:
                - 'nearest' (default)
                - 'bilinear'
                - 'bicubic'
                - 'cubic'            
    """

    # check if outfile exists and delete it:
    path = os.path.dirname(image)
    
    if outPath == None:
        if outName in os.listdir(path):
            print 'Outfile already exists, will be overwritten!'
            os.remove(os.path.join(path, outName))
    else:
        if outName in os.listdir(outPath):
            print 'Outfile already exists, will be overwritten!'
            os.remove(os.path.join(outPath, outName))
            
    gdal.AllRegister()
    
    driver = gdal.GetDriverByName(outFormat)
    
    ds = gdal.Open(image, GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    # open mask image:
    maskds = gdal.Open(maskImage, GA_ReadOnly)
    maskBand = maskds.GetRasterBand(1)
    mask = maskBand.ReadAsArray(0, 0, maskds.RasterXSize, maskds.RasterYSize)
    
    # create (empty) output image:
    if outExtent == 'image':
        if outPath == None:
            ds_out = driver.Create(os.path.join(path, outName), \
                    ds.RasterXSize, ds.RasterYSize, bands, \
                    ds.GetRasterBand(1).DataType)
        else:
            ds_out = driver.Create(os.path.join(outPath, outName), \
                        ds.RasterXSize, ds.RasterYSize, bands, \
                        ds.GetRasterBand(1).DataType)
                        
        ds_out.SetProjection(ds.GetProjection())
        ds_out.SetGeoTransform(ds.GetGeoTransform())
            
    else:
        if outPath == None:
            ds_out = driver.Create(os.path.join(path, outName), \
                    maskds.RasterXSize, maskds.RasterYSize, bands, \
                    band.DataType)
        else:
            ds_out = driver.Create(os.path.join(outPath, outName), \
                        maskds.RasterXSize, maskds.RasterYSize, bands, \
                        band.DataType)

        ds_out.SetProjection(maskds.GetProjection())
        ds_out.SetGeoTransform(maskds.GetGeoTransform())

    # apply mask to all bands:
    for b in xrange(1, bands + 1):
        band = ds.GetRasterBand(b)
        data = band.ReadAsArray(0, 0, cols, rows)
        # if mask and image have different size, resample one of them depending
        # on users choice:
        if mask.shape != data.shape:
            if outExtent == 'image':
                re_mask = misc.imresize(mask, data.shape, interp=interpolation)
                data_out = re_mask * data
            else:
                re_data = misc.imresize(data, mask.shape, interp=interpolation)
                data_out = mask * re_data
        
        else:
            data_out = mask * data
        # write masked band:
        b_out = ds_out.GetRasterBand(b)
        b_out.WriteArray(data_out)

        b_out = None
        
        pr.progress(b, xrange(1, bands + 1))
    
    ds_out = None
    ds = None
