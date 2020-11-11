#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
date: Tue Jan 19 11:25:19 2016
user: hendrik
"""

import os
import sys
import string
from osgeo import gdal
from osgeo.gdalconst import *

try:
    import progress_bar as pr
except:
    pass
   
   
##################
### Layerstack ###
##################

def stack_images(images, outfile, bands=None, of='GTiff', co=None, noData=0, bandNames=None):
    
    """
    Create a layerstack from all files within a directory.
    
    Use:
    
    images (list): a list of strings containing the full path and file 
            extension for the single raster files which shall be stacked 
            together. Will be stacked in the order as given by this list.
    
    outfile (string): the name of the output file (full path and file 
            extension).
    
    bands (list): a list containing the desired band numbers of the input 
            images which shall be used for stacking. By this, single bands out 
            of multiband images can be used. Defaults to "None", which means 
            that the first band will be used. If more than one band from the 
            same multiband image shall be used, the filename must be given 
            again in the "images"-list.
    
    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
    
    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.
            
            Example:
                createOptions=['interleave=bil']
        
    noData (int / float): the no-data value to be set. Defaults to the no-data 
            value of the first input file.
            
    bandNames (list): a list of band names for the output file. Defaults to the
            names of the input files.
    """
        
    gdal.AllRegister()
    # get basic information and create output raster:
    ds = gdal.Open(images[0], GA_ReadOnly)
    band = ds.GetRasterBand(1)
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()
    x = ds.RasterXSize
    y = ds.RasterYSize
    dtype = band.DataType
    # nodata
    if noData == None:
        nodata = band.GetNoDataValue()
    else:
        nodata = noData
        
    driver = gdal.GetDriverByName(of)
    # check for create options
    if co == None:
        ds_out = driver.Create(outfile, x, y, len(images), dtype)
    else:
        ds_out = driver.Create(outfile, x, y, len(images), dtype, co)
    # set projection
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(transform)
    band = None
    ds = None
    # loop through all files and stack them:
    band_index = 1
    
    for name in images:
        # progress bar:
        try:
            pr.progress(name, images)
        except:
            pass
        # open imput image
        ds = gdal.Open(name, GA_ReadOnly)
        # check if specific bands are desired
        if bands == None:
            band = ds.GetRasterBand(1)
        else:
            band = ds.GetRasterBand(bands[band_index-1])
        # set data type
        dtype = band.DataType
        # read data
        data = band.ReadRaster(0, 0, x, y, x, y, dtype)
        band_out = ds_out.GetRasterBand(band_index)
        # create new band names (either from original image or from user input):
        if bandNames == None:
            band_out.SetDescription(band.GetDescription())
        else:
            band_out.SetDescription(bandNames[band_index - 1])
            
        band_out.SetNoDataValue(nodata)
        band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
        
        band_index += 1
        
        band = None
        ds = None
    
    ds_out = None


######################
### Band insertion ###
######################

# Still missing: BAND SUBSTITUION

def insert_band(raster, layer, outName, bandIndex=None, substitute=False, \
                bandNames=None, outFormat=None, createOptions=None):
    
    
    """
    Insert raster layers into a multiband image at desired positions.
    
    Use:
    
    raster (string): the name of the output file (full path and file extension).
    
    layer (string / list): EITHER the name of the input raster containing the 
            layer to be inserted (full path and file extension)
            OR
            a list containing all (single-band) rasters to be inserted.
    
    outName (string): the name of the output file (full path and file extension).
    
    bandIndex (integer / list): EITHER a single value indicating the position
            for the layer
            OR
            a list of integers containing all positions.
            Per default, the layer(s) is/are inserted at the end.
    
    substitute (boolean): if set "True", the layers to be inserted will 
            substitute the existing one at their resprective positions. Defaults
            to "False", which means that the new layers will be inserted at the 
            desired position and all other bands will be appended afterwards.
            Substitution will not work if "bandIndex" ist not set!
    
    bandNames (list): a list of band names for the inserted layers. Defaults to 
            the names of the input files.
    
    outFormat (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to the format of the input raster.
    
    createOptions (list): a list of strings, containing advanced raster creation 
            options such as band interleave.
            
            Example:
                createOptions=['interleave=bil']
    """
    
    gdal.AllRegister()
    
     # get basic information and create output raster:
    ds = gdal.Open(raster, GA_ReadOnly)    
    bands = ds.RasterCount

    band = ds.GetRasterBand(1)
    x = ds.RasterXSize
    y = ds.RasterYSize
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()
    meta = ds.GetMetadata_Dict()
    
    if isinstance(layer, basestring) == True:
        layer = list(layer)
    
    if bandIndex != None:
        if isinstance(bandIndex, list) == False:
            newBands = list(bandIndex)
        else:
            newBands = bandIndex
    else:
        newBands = [i for i in xrange(bands + 1, bands + (len(layer) + 1))]
    
    if bandNames != None:
        if isinstance(bandNames, list) == False:
            bandNames = list(bandNames)
        else:
            bandNames = bandNames

    if outFormat == None:
        outFormat = ds.GetDriver().GetDescription()
    else:
        outFormat = outFormat
    
    driver = gdal.GetDriverByName(outFormat)
    
    if createOptions == None:
        ds_out = driver.Create(outName, x, y, bands + len(newBands), band.DataType)
    else:
        ds_out = driver.Create(outName, x, y, bands + len(newBands), band.DataType, \
                                createOptions)
                               
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(transform)
    
    band = None
    
    if bandIndex != None:
        lyr_index = 1
        band_index = 1
        # insert single layers at desired positions
        for b in xrange(1, bands + 1):
            # progress bar:
            try:
                pr.progress(b, xrange(1, bands + 1))
            except:
                pass
    
            if b in newBands:
                insert = gdal.Open(layer[lyr_index - 1], GA_ReadOnly)
                band = insert.GetRasterBand(1)
                dtype = band.DataType
                nodata = band.GetNoDataValue()
                
                data = band.ReadRaster(0, 0, x, y, x, y, dtype)
                band_out = ds_out.GetRasterBand(band_index)
                
                # create new band names (either from original image or from user input):
                if bandNames == None:
                    name = string.join(['Band', str(band_index)], sep='_')
                    desc = band.GetDescription()
                    if len(desc) == 0:
                        desc = layer[lyr_index - 1]
                    meta[name] = desc
                    band_out.SetDescription(band.GetDescription())
                else:
                    name = string.join(['Band', str(band_index)], sep='_')
                    meta[name] = bandNames[lyr_index - 1]
                    band_out.SetDescription(bandNames[lyr_index - 1])
             
                band_out.SetNoDataValue(double(nodata))
                band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
                
                lyr_index += 1
                
                if substitute == False:
                    band_index += 1
                
                insert = None
                
                # then next band of original image:
                band = ds.GetRasterBand(b)
                dtype = band.DataType
                nodata = band.GetNoDataValue()
               
                data = band.ReadRaster(0, 0, x, y, x, y, dtype)
                band_out = ds_out.GetRasterBand(b)
                
                name = string.join(['Band', str(band_index)], sep='_')
                meta[name] = band.GetDescription()
                band_out.SetDescription(band.GetDescription())
                
                band_out.SetNoDataValue(double(nodata))
                band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
                
                band_index += 1
                
                band_out = None
                band = None
                
            else:
                band = ds.GetRasterBand(b)
                dtype = band.DataType
                nodata = band.GetNoDataValue()
               
                data = band.ReadRaster(0, 0, x, y, x, y, dtype)
                band_out = ds_out.GetRasterBand(b)
                
                name = string.join(['Band', str(band_index)], sep='_')
                meta[name] = band.GetDescription()
                band_out.SetDescription(band.GetDescription())
    
                band_out.SetNoDataValue(double(nodata))
                band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
                
                band_index += 1
            
                band_out = None
                band = None
                
    else:
        if substitute == True:
            raise ValueError("Option 'substitute' will only work with 'bandIndex' set!")
            
        lyr_index = 1
        band_index = 1
    # insert single layers at the end
        for b in xrange(1, bands + 1):
            band = ds.GetRasterBand(b)
            dtype = band.DataType
            nodata = band.GetNoDataValue()
           
            data = band.ReadRaster(0, 0, x, y, x, y, dtype)
            band_out = ds_out.GetRasterBand(b)
            
            name = string.join(['Band', str(band_index)], sep='_')
            meta[name] = band.GetDescription()
            band_out.SetDescription(band.GetDescription())
    
            band_out.SetNoDataValue(double(nodata))
            band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
            
            band_index += 1
        
            band_out = None
            band = None
            
        for i in xrange(0, len(newBands)):
            insert = gdal.Open(layer[i], GA_ReadOnly)
            band = insert.GetRasterBand(1)
            dtype = band.DataType
            nodata = band.GetNoDataValue()
                
            data = band.ReadRaster(0, 0, x, y, x, y, dtype)
            band_out = ds_out.GetRasterBand(band_index)
            
            # create new band names (either from original image or from user input):
            if bandNames == None:
                name = string.join(['Band', str(band_index)], sep='_')
                desc = band.GetDescription()
                if len(desc) == 0:
                    desc = layer[lyr_index - 1]
                meta[name] = desc
                band_out.SetDescription(band.GetDescription())
            else:
                name = string.join(['Band', str(band_index)], sep='_')
                meta[name] = bandNames[lyr_index - 1]
                band_out.SetDescription(bandNames[lyr_index - 1])
             
                band_out.SetNoDataValue(double(nodata))
                band_out.WriteRaster(0, 0, x, y, data, x, y, dtype)
                
                lyr_index += 1
                band_index += 1
        
    ds_out.SetMetadata(meta)
    
    ds_out = None
    ds = None
