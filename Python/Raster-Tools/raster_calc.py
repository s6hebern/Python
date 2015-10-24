# -*- coding: utf-8 -*-

from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np

def raster_calc(a, b, outfile, mode, band_a=None, band_b=None, of='GTiff', co=None):
    
    """
    Combine two rasters based on one of the four basic arithmetic operations.
    
    
    Use:
    
    a (string): first input image (full path and file extension). May contain 
            multiple bands.
    
    b (string): second input image (full path and file extension). May contain 
            multiple bands.
    
    outfile (string): the output image (full path and file extension).
    
    mode (string): the arithmetic operation. Must be one of:
            - 'add'
            - 'subtract'
            - 'multiply'
            - 'divide'
    
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
                createOptions=['interleave=bil']
    """    


    gdal.AllRegister()
    driver = gdal.GetDriverByName(of)

    # read data:    
    ds_a = gdal.Open(a, GA_ReadOnly)
    ds_b = gdal.Open(b, GA_ReadOnly)

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
