# -*- coding: utf-8 -*-

from osgeo import ogr, gdal, gdal_array
from gdalconst import *
import os
import string
import numpy as np
import re

try:
    import progress_bar as pr
except:
    pass
    
def point_sampling(raster, shape, bands=None, dataType=ogr.OFTInteger, winRad=0, \
        mode='median', noDataValue=None, removeValue=None, precision=None, \
        names=None):
    
    """
    Point sampling of a point shapefile and an image file. Creates a new 
    attribute field for each raster band containing the values at the respective
    point positions or the desired statistical value within a window around 
    these positions.
    
    Use:
    
    raster (string): the image file (full path and file extension).
            
    shape (string): the shapefile (full path and file extension) containing the 
            points at which positions the raster shall be sampled.
    
    bands (list): a list of integers containing the numbers of the desired 
            bands to be sampled. Defaults to "None", which means that all bands
            will be used. Counting starts at 1.
            
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
                - 'majority' (most frequent value, only for integer values)
    
    noDataValue (integer): the desired nodata-value, if the input image does not
            have one or it shall be changed for the shapefile.
    
    removeValue (integer): the nodata-value of the input image, which will be deleted
            from the sampling window before calculating the desired statistic.
            Defaults to NONE (which means that no value shall be deleted).
            
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
    # check if specific bands are desired
    if bands == None:
        bands = xrange(rst.RasterCount)
    else:
        bands = bands
    # get raster information
    xSize = rst.RasterXSize
    ySize = rst.RasterYSize
    geotrans = rst.GetGeoTransform()
    xyOrigin = (geotrans[0], geotrans[3])
    pixWidth = geotrans[1]
    pixHeight = geotrans[5]
    # open shape
    shape = shape
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp = driver.Open(shape, 1)
    lyr = shp.GetLayer()
    # get points:
    points = [(p.GetGeometryRef().GetX(), p.GetGeometryRef().GetY()) for p in lyr]
    # loop through all bands, create fields and write values:
    for f in xrange(len(bands)):
        # progress bar
        try:
            pr.progress(f, xrange(len(bands)))
        except:
            pass
        # get band
        if bands == None:
            b = rst.GetRasterBand(bands[f] + 1)
        else:
            b = rst.GetRasterBand(bands[f])
        dt = b.DataType
        # create field names
        if names == None:
            # get band name and create field name (max length is 10 characters)
            bName = b.GetDescription()
            bName = re.sub(r'[^a-zA-Z0-9_-]', r'', str(bName))
            if len(bName) > 10:
                bName = bName[0:10]
        else:
            bName = names[f]
        # get maximum value to set field width (valid values only):
        maxVal = int(b.ComputeRasterMinMax()[1])
        b = None
        # check if fields already exist:
        if bName in lyr.GetFeature(0).keys():
            pass
        else:
            field = ogr.FieldDefn(bName, dataType)
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
            band = rst.GetRasterBand(bands[f] + 1)
            noData = band.GetNoDataValue()
            if noData == None and noDataValue != None:
                noData = noDataValue
            elif noData == None and noDataValue == None:
                noData = 0
            # get value at the desired position (or window):
            if winRad == 0:
                data = band.ReadAsArray(xOff, yOff, 1, 1)
            else:
                xOff = xOff - winRad
                yOff = yOff - winRad
                # check if window origin still within raster:
                if xOff < 0:
                    winX = winRad * 2 - abs(xOff)
                    xOff = 0
                    
                if yOff < 0:
                    winY = winRad * 2 - abs(yOff)
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
                # delete desired removeValue from window:
                if removeValue != None:
                    #dt = gdal_array.GDALTypeCodeToNumericTypeCode(dt)
                    dt = type(window[0, 0])
                    window = window[window != dt(removeValue)]
                if window.size == 0:
                    data = noData
                else:
                    # calculate desired statistic:
                    if mode == 'median':
                        data = np.median(np.ma.masked_invalid(window))
                    elif mode == 'mean':
                        data = np.nanmean(np.ma.masked_invalid(window))
                    elif mode == 'min':
                        data = np.nanmin(np.ma.masked_invalid(window))
                    elif mode == 'max':
                        data = np.nanmax(np.ma.masked_invalid(window))
                    elif mode == 'majority':
                        data = np.bincount(window.flatten()).argmax()
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
            feat.SetField(bName, val)
            lyr.SetFeature(feat)
            feat = None
    # clean up
    rst = None
    lyr = None
    shp = None
