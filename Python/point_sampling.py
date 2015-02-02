# -*- coding: utf-8 -*-

from osgeo import ogr, gdal
from gdalconst import *
import os
import string
import numpy as np
import re

try:
    import module_progress_bar as pr
except:
    pass
    
def point_sampling(raster, shape, dataType=ogr.OFTInteger, winRad=0, mode='median', precision=None, names=None):
    
    """
    Point sampling of a point shapefile and an image file. Creates a new 
    attribute field for each raster band containing the values at the respective
    point positions or the desired statistical value within a window around 
    these positions.
    
    Use:
    
    raster (string): the image file (full path and file extension).
            
    shape (string): the shapefile (full path and file extension) containing the 
            points at which positions the raster shall be sampled.
            
    dataType (ogr DataType): the ogr data type of the output fields which shall 
            be created. Takes only ogr.OFTInteger (default) and ogr.OFTReal.
            
    winRad (integer): the radius of the window around the respective point 
            position. For example, a value of 4 will create a window of 8x8 
            pixels (4 pixels to each direction). Defaults to 0, which means that 
            the value will be taken from the exact point position.
            If a point lies so close to the edges of the raster that the origin 
            of the sampling window would be outside the raster, it will be moved 
            right to the raster's edge. It will then also be resized to the 
            remainder of the originally desired size.
            If the origin of the sampling window is inside the raster, but the
            window would cross the edges, it will also be resized to the maximum
            possible size.
            
    mode (string): the statistical value which shall be taken from the window. 
            Possible values are:
                - 'median' (default)
                - 'mean'
                - 'min'
                - 'max'
            
    precision (integer): the precision of the output attribute field, if 
            floating numbers are desired. If not specified, precision will be 
            set to the length of the maximum value.
            
    names (list): a list of the field names for the output attribute fields, 
            with a maximum length of 10 characters. If not specified, the band 
            names of the raster file will be taken as field names. If they 
            contain characters which are not within (a-z, A-Z, 0-9, _, -) those 
            will be deleted. If the raster file has no band names, they will be
            created as 'Band_1', 'Band_2', etc.
    """

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
    if bandNames == []:
        bandNames = [string.join(['Band', str(i)], sep='_') for i in xrange(1, \
                                                                    bands + 1)]
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
        
        pr.progress(f, xrange(bands))
        
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
                xOff = xOff - winRad
                yOff = yOff - winRad
                # check if window origin still within raster:
                if xOff < 0:
                    winX = winRad - xOff
                    xOff = 0
                    
                if yOff < 0:
                    winY = winRad - yOff
                    yOff = 0
                # check if window size still fits into raster without crossing 
                # the edges. If not, set window size to maximum possible value:
                if xOff + (winRad * 2) > xSize:
                    winX = xSize - xOff
                else:
                    winX = winRad * 2
                    
                if yOff + (winRad * 2) > ySize:
                    winY = ySize - yOff
                else:
                    winY = winRad * 2
                # get data within desired window:
                window = band.ReadAsArray(xOff, yOff, winX, winY)

                # calculate desired statistic:
                if mode == 'median':
                    data = np.median(np.ma.masked_invalid(window))
                elif mode == 'mean':
                    data = np.nanmean(np.ma.masked_invalid(window))
                elif mode == 'min':
                    data = np.nanmin(np.ma.masked_invalid(window))
                elif mode == 'max':
                    data = np.nanmax(np.ma.masked_invalid(window))
            # convert to desired data type:
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
