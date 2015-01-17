# -*- coding: utf-8 -*-

"""
    Point sampling of a point shapefile and an image file. Creates a new 
    attribute field for each raster band containing the values at the respective
    point positions or the desired statistical value within a window around 
    these positions.
    
    Use:
    
    raster: the image file (full path and file extension), may contain multiple
            bands.
            
    shape: the shapefile (full path and file extension) containing the points at 
            which positions the raster shall be sampled.
            
    dataType: the ogr data type of the output fields which shall be created. 
            Takes only ogr.OFTInteger (default) and ogr.OFTReal.
            
    winRad: the radius of the window around the respective point position. For
            example, a value of 4 will create a window of 8x8 pixels (4 pixels
            to each direction). If not specified, no window will be used and the
            value will be taken from the exact point position.
            
    mode: the statistical value which shall be taken from the window, given as
            string. Possible values are:
                - 'median' (default)
                - 'mean'
                - 'min'
                - 'max'
            
    precision: the precision of the output attribute field, if floating numbers
            are desired. If not specified, precision will be set to the length 
            of the maximum value.
            
    names: the field names of the output attribute fields, with a maximum length
            of 10 characters, given as a list. If not specified, the band names 
            of the raster file will be taken as field names. If they contain 
            characters which are not within (a-z, A-Z, 0-9, _, -) those will be 
            deleted.
"""

from osgeo import ogr, gdal
from gdalconst import *
import os
import numpy as np
import re

try:
    import module_progress_bar as pr
except:
    pass
    
def point_sampling(raster, shape, dataType=ogr.OFTInteger, winRad=0, mode='median', precision=None, names=None):

    raster = raster
    rst = gdal.Open(raster, GA_ReadOnly)
    bands = rst.RasterCount
    xSize = rst.RasterXSize
    ySize = rst.RasterYSize
    geotrans = rst.GetGeoTransform()
    xyOrigin = (geotrans[0], geotrans[3])
    pixWidth = geotrans[1]
    pixHeight = geotrans[5]
    
    shape = shape
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp = driver.Open(shape, 1)
    lyr = shp.GetLayer()
    
    # get points:
    points = [(p.GetGeometryRef().GetX(), p.GetGeometryRef().GetY()) for p in lyr]
    
    # create field names from raster band names:
    bandNames = sorted(rst.GetMetadata().values())
    bandNames.remove('Area')
    # delete characters which are not in the following list:
    bandNames = [re.sub(r'[^a-zA-Z0-9_-]', r'', str(i)) for i in bandNames]
    
    fieldNames = []
    
    if names == None:
        # fields in shapefiles may contain a maximum of 10 characters:
        for name in bandNames:
            if len(name) > 10:
                fieldNames.append(name[0:10])
            else:
                fieldNames.append(name)
    else:
        fieldNames = [re.sub(r'[^a-zA-Z0-9_-]', r'', str(i)) for i in names]
    
    # loop through all bands, create fields and write values:
    for f in xrange(bands):
        # progress bar:
        try:
            pr.progress(f, xrange(bands))
        except:
            pass
        
        b = rst.GetRasterBand(f + 1)
        # check for invalid values:
        maxVal = int(round(np.nanmax(np.ma.masked_invalid(b.ReadAsArray(0, 0, \
                                                            xSize, ySize)))))
        b = None
        # check if fields already exist:
        if str(fieldNames[f]) in lyr.GetFeature(0).keys():
            pass
        else:
            field = ogr.FieldDefn(str(fieldNames[f]), dataType)
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
            noData = band.GetNoDataValue()
            # get value at the desired position (or window):
            if winRad == 0:
                data = band.ReadAsArray(xOff, yOff, 1, 1)
            else:
                if mode == 'median':
                    data = np.median(np.ma.masked_invalid(band.ReadAsArray( \
                            xOff - winRad, yOff - winRad, winRad * 2, winRad * 2)))
                elif mode == 'mean':
                    data = np.nanmean(np.ma.masked_invalid(band.ReadAsArray( \
                            xOff - winRad, yOff - winRad, winRad * 2, winRad * 2)))
                elif mode == 'min':
                    data = np.nanmin(np.ma.masked_invalid(band.ReadAsArray( \
                            xOff - winRad, yOff - winRad, winRad * 2, winRad * 2)))
                elif mode == 'max':
                    data = np.nanmax(np.ma.masked_invalid(band.ReadAsArray( \
                            xOff - winRad, yOff - winRad, winRad * 2, winRad * 2)))
                                                    
            if dataType == ogr.OFTInteger and data != None:
                val = int(data)
            elif dataType == ogr.OFTInteger and data == None:
                val = int(noData)
            elif dataType == ogr.OFTReal and data != None:
                val = float(data)
            elif dataType == ogr.OFTReal and data == None:
                val = int(noData)
            else:
                raise(Warning('Invalid Data Type assigned! Function takes only ogr.OFTInteger and ogr.OFTReal'))
            # set value:
            feat = lyr.GetFeature(point)
            feat.SetField(str(fieldNames[f]), val)
            lyr.SetFeature(feat)
            feat = None
    
    rst = None
    lyr = None
    shp = None
