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

    # create output image with the desired number of bands:
    if createOptions != None:
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, len(bands), \
                                band.DataType, createOptions)
    else:
        ds_out = driver.Create(out, ds.RasterXSize, ds.RasterYSize, len(bands), \
                                band.DataType)

    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(transform)
    
    band = None
    
    # get desired bands from input image and write them to the new file:
    band_index = 1
    # new dictionary for metadata:
    meta = {}
    
    for b in xrange(len(bands)):
        try:
            pb.progress(bands[b], bands)
        except:
            pass
        
        band = ds.GetRasterBand(bands[b])

        dtype = band.DataType
        data = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize, \
                               ds.RasterXSize, ds.RasterYSize, dtype)
        band_out = ds_out.GetRasterBand(band_index)

        # create new band names (either from original image or from user input):
        if bandNames == None:
        	name = string.join(['Band', str(bands[b])], sep='_')
        	meta[name] = band.GetDescription()
        	band_out.SetDescription(band.GetDescription())
        else:
        	name = string.join(['Band', str(bands[b])], sep='_')
        	meta[name] = bandNames[b]
        	band_out.SetDescription(bandNames[b])

        if nodata != None:
            band_out.SetNoDataValue(nodata)
        band_out.WriteRaster(0, 0, ds.RasterXSize, ds.RasterYSize, data,
                             ds.RasterXSize, ds.RasterYSize, dtype)
        band = None
        band_index += 1
    
    ds_out.SetMetadata(meta)

    ds_out = None
    ds = None


def multi_to_single(image, out=None, outFormat='GTiff', noData=None, \
                    createOptions=None):
    
    """
    Split a multiband image into many singleband images.
    
    Use:
    
    image (string): the input image which shall be subsetted (full path and file
            extension).
    
    out (string): the name of the output file (full path and file extension). 
            The band number will be appended at the end ('*_X.*'). Defaults to
            the file name of the inpur image.

    outFormat (string): the desired format of the output file as provided by the
            GDAL raster formats (see: http://www.gdal.org/formats_list.html).
            Defaults to 'GTiFF'.
     
    noData (int / float): the no-data value to be set. Defaults to the no-data
            value of the first input file.
               
    createOptions (list): a list of strings, containing advanced raster creation
            options such as band interleave.
            
            Example:
            createOptions=['interleave=bil']
    """
    
    gdal.AllRegister()
    driver = gdal.GetDriverByName(outFormat)
    
    ds = gdal.Open(image, GA_ReadOnly)
    
    bands = ds.RasterCount
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()

    # create singleband output images:
    for b in xrange(1, bands + 1):
        try:
            pb.progress(b, xrange(1, bands + 1))
        except:
            pass
        
        # create output names with coorect numbering:
        if out == None:
            if len(str(bands)) - len(str(b)) == 1:
                name = string.join([os.path.splitext(image)[0], '_0', str(b), \
                    os.path.splitext(image)[1]], sep='')
            elif len(str(bands)) - len(str(b)) == 2:
                name = string.join([os.path.splitext(image)[0], '_00', str(b), \
                    os.path.splitext(image)[1]], sep='')
            elif len(str(bands)) - len(str(b)) == 3:
                name = string.join([os.path.splitext(image)[0], '_000', str(b), \
                    os.path.splitext(image)[1]], sep='')
            else:
                name = string.join([os.path.splitext(image)[0], '_', str(b), \
                    os.path.splitext(image)[1]], sep='')
        else:
            if len(str(bands)) - len(str(b)) == 1:
                name = string.join([os.path.splitext(out)[0], '_0', str(b), \
                    os.path.splitext(out)[1]], sep='')
            elif len(str(bands)) - len(str(b)) == 2:
                name = string.join([os.path.splitext(out)[0], '_00', str(b), \
                    os.path.splitext(out)[1]], sep='')
            elif len(str(bands)) - len(str(b)) == 3:
                name = string.join([os.path.splitext(out)[0], '_000', str(b), \
                    os.path.splitext(out)[1]], sep='')
            else:
                name = string.join([os.path.splitext(out)[0], '_', str(b), \
                    os.path.splitext(out)[1]], sep='')

        band = ds.GetRasterBand(b)
        
        if noData == None:
            nodata = band.GetNoDataValue()
        else:
            nodata = noData
        
        if createOptions != None:
            ds_out = driver.Create(name, ds.RasterXSize, ds.RasterYSize, 1, \
                                    band.DataType, createOptions)
        else:
            ds_out = driver.Create(name, ds.RasterXSize, ds.RasterYSize, 1, \
                                    band.DataType)
        
        ds_out.SetProjection(proj)
        ds_out.SetGeoTransform(transform)

        dtype = band.DataType
        data = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize, \
                               ds.RasterXSize, ds.RasterYSize, dtype)
        band_out = ds_out.GetRasterBand(1)

        # create metadata, write output:
        meta = {}
        name = string.join(['Band', str(b)], sep='_')
        meta[name] = band.GetDescription()
        band_out.SetDescription(band.GetDescription())
        
        if nodata != None:
            band_out.SetNoDataValue(nodata)
        
        band_out.WriteRaster(0, 0, ds.RasterXSize, ds.RasterYSize, data,
                             ds.RasterXSize, ds.RasterYSize, dtype)
            
        band = None
        band_out = None

        ds_out.SetMetadata(meta)

        ds_out = None
        
    ds = None
