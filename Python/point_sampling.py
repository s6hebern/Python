# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 09:51:11 2014

@author: Hendrik
"""

"""
    Point sampling of a point shapefile and an image file. Creates a new 
    attribute field for each raster band containing the values at the respective
    point positions.
    
    Use:
    
    raster: the image file (full path and file extension), may contain multiple
            bands.
            
    shape: the shapefile (full path and file extension) containing the points at 
            which positions the raster shall be sampled.
            
    dataType: the ogr data type of the output fields which shall be created. 
            Takes only ogr.OFTInteger and ogr.OFTReal.
            
    precision: the precision of the output attribute field, if floating numbers
            are desired. If not specified, precision will be set to the length 
            of the maximum value.
            
    names: the field names of the output attribute fields, with a maximum length
            of 10 characters. If not specified, the band names of the raster 
            file will be taken as field names. If they contain characters which
            are not in the following list, those characters will be deleted.
            (a-z, A-Z, 0-9, _, -)
"""

from osgeo import ogr, gdal
from gdalconst import *
import os
import numpy as np
import re
    
def point_sampling(raster, shape, dataType, precision=None, names=None):

    raster = raster
    rst = gdal.Open(raster, GA_ReadOnly)
    bands = rst.RasterCount
    xSize = rst.RasterXSize
    ySize = rst.RasterYSize
    geotrans = rst.GetGeoTransform()
    xyOrigin = (geotrans[0], geotrans[3])
    pixWidth = geotrans[1]
    pixHeight = geotrans[5]
    #maxVal = int(round(rst.ReadAsArray().max()))
    
    shape = shape
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp = driver.Open(shape, 1)
    lyr = shp.GetLayer()
    
    # get points:
    points = [(p.GetGeometryRef().GetX(), p.GetGeometryRef().GetY()) for p in lyr]
    
    # create field names from raster band names:
    bandNames = sorted(rst.GetMetadata().values())[0:len(rst.GetMetadata().values())]
    # delete characters which are not in the following list:
    bandNames = [re.sub(r'[^a-zA-Z0-9_-]', r'', i) for i in bandNames]
    
    fieldNames = []
    
    if names == None:
        # fields in shapefiles may contain a maximum of 10 characters:
        for name in bandNames:
            if len(name) > 10:
                fieldNames.append(name[0:10])
            else:
                fieldNames.append(name)
    else:
        fieldNames = names
    
    # loop through all bands, create fields and write values:
    for f in xrange(bands):
        b = rst.GetRasterBand(f + 1)
        maxVal = int(round(b.ReadAsArray(0, 0, xSize, ySize).max()))
        b = None
        # check if fields already exist:
        if fieldNames[f] in lyr.GetFeature(0).keys():
            pass
        else:
            field = ogr.FieldDefn(fieldNames[f], dataType)
            if precision == None:
                field.SetWidth(len(str(maxVal)))
            else:
                field.SetWidth(len(str(maxVal)) + precision + 1)
                field.SetPrecision(precision)
            lyr.CreateField(field)
        
        # loop through all points and get values:
        for point in xrange(len(points)):
            # compute offset:
            xOff = int((points[point][0] - xyOrigin[0]) / pixWidth)
            yOff = int((points[point][1] - xyOrigin[1]) / pixHeight)
            # get band:
            band = rst.GetRasterBand(f + 1)
            data = band.ReadAsArray(xOff, yOff, 1, 1)
            if dataType == ogr.OFTInteger:
                val = int(data[0, 0])
            elif dataType == ogr.OFTReal:
                val = float(data[0, 0])
            else:
                raise(Warning('Invalid Data Type assigned! Function takes only ogr.OFTInteger and ogr.OFTReal'))
            # set value:
            feat = lyr.GetFeature(point)
            feat.SetField(fieldNames[f], val)
            lyr.SetFeature(feat)
            feat = None
    
    rst = None
    lyr = None
    shp = None
