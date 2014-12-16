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
            are desired. If not set, precision will not be set and may raise an
            error.
            
    names: the field names of the output attribute fields, with a maximum lentgh
            of 10 characters. If not set, the band names of the raster file will
            be taken as field names.
"""

from osgeo import ogr, gdal
from gdalconst import *
import os
import numpy as np
    
def point_sampling(raster, shape, dataType, precision=None, names=None):

    raster = raster
    rst = gdal.Open(raster, GA_ReadOnly)
    bands = rst.RasterCount
    geotrans = rst.GetGeoTransform()
    xyOrigin = (geotrans[0], geotrans[3])
    pixWidth = geotrans[1]
    pixHeight = geotrans[5]
    maxVal = int(round(rst.ReadAsArray().max()))
    
    shape = shape
    driver = ogr.GetDriverByName("ESRI Shapefile")
    shp = driver.Open(shape, 1)
    lyr = shp.GetLayer()
    
    # get points:
    points = [(p.GetGeometryRef().GetX(), p.GetGeometryRef().GetY()) for p in lyr]
    
    # create field names from raster band names:
    bandNames = sorted(rst.GetMetadata().values())[0:len(rst.GetMetadata().values())-1]
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
