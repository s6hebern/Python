# -*- coding: utf-8 -*-

import os
import sys
import string
from osgeo import gdal
from osgeo.gdalconst import *
try:
    import module_progress_bar as pb
except:
    pass

def spectral_subset(image, bands, out, outFormat='GTiff', createOptions=None, \
        noData=None, bandNames=None):
    
    """
    Create a spectral subset of a multiband image.
    
    Use:
    
    image (string): the input image which shall be subsetted (full path and file
            extension).
    
    bands (list): a list of integers of the desired band numbers to keep. 
            Counting starts at 1.
    
    out (string): the name of the output file (full path and file extension).
    
    outFormat (string): the desired format of the output file as provided by the
            GDAL raster formats (see: http://www.gdal.org/formats_list.html).
            Defaults to 'GTiFF'.
                
    createOptions (list): a list of strings, containing advanced raster creation
            options such as band interleave.
            
            Example:
            createOptions=['interleave=bil']
    
    noData (int / float): the no-data value to be set. Defaults to the no-data
            value of the first input file.

    bandNames (list): a list of band names for the output file. Defaults to the
            names of the input files.
    """
    
    gdal.AllRegister()
    driver = gdal.GetDriverByName(outFormat)
    
    ds = gdal.Open(image, GA_ReadOnly)
    # get basic information:
    band = ds.GetRasterBand(1)
    
    if noData == None:
        nodata = band.GetNoDataValue()
    else:
        nodata = noData
    
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()
    ds_meta = ds.GetMetadata()
    # create new band names (either from original image or from user input):
    meta = {}

    if bandNames == None:
        count = 1
        for b in bands:
            name = string.join(['Band', str(b)], sep='_')
            for key in ds_meta.keys():
                if name == key:
                    new_name = string.join(['Band', str(count)], sep='_')
                    meta[new_name] = ds_meta[key]
                    count += 1
    else:
        count = 1
        for n in bandNames:
            new_name = string.join(['Band', str(count)], sep='_')
            meta[new_name] = str(n)
            count += 1
    
    # create output image with the desired number of bands:
    if createOptions != None:
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, len(bands), \
                                band.DataType, createOptions)
    else:
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, len(bands), \
                                band.DataType)
        
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(transform)
    ds_out.SetMetadata(meta)
    
    band = None
    
    # get desired bands from input image and write them to the new file:
    band_index = 1
    
    for b in bands:
        try:
            pb.progress(b, bands)
        except:
            pass
        
        band = ds.GetRasterBand(b)
        dtype = band.DataType
        data = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize, \
                               ds.RasterXSize, ds.RasterYSize, dtype)
        band_out = ds_out.GetRasterBand(band_index)
        if nodata != None:
            band_out.SetNoDataValue(nodata)
        band_out.WriteRaster(0, 0, ds.RasterXSize, ds.RasterYSize, data,
                             ds.RasterXSize, ds.RasterYSize, dtype)
        band = None
        band_index += 1
    
    ds_out = None
    ds = None
