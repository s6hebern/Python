# -*- coding: utf-8 -*-

import os
import sys
import string
from osgeo import gdal
from osgeo.gdalconst import *
import numpy as np
from scipy import misc

try:
    import progress_bar as pr
except:
    pass


###################
### CREATE MASK ###
###################

def create_mask(image, values, valRange=True, dataBand=None, outName=None, \
                outPath=None, of='GTiff', co=None, nodata=None):
    """
    Create a binary mask (containing only 0 and 1) from an image (which may 
            contain more than one band).

    Use:

    image (string): the image file (full path and file extension).

    values (list): a list containing the minimum (first entry) and maximum 
            (second entry) values of the data range which shall be set to 1. If
            only one entry is given, this value will be set to 1, all others to
            0.

    valRange (boolean): Defaults to 'True', which means that a range of two 
            values is given (minimum and maximum). If set to 'False', the exact
            values of the given list will be taken to set to 1.

    dataBand (integer): the band number of the desired band to use, if the input
            image contains more than one band.

    outName (string): the name of the output file (with file extension). 
            Defaults to the name of the input image, extended by '_mask'.

    outpath (string): the directory to which the output file will be written. 
            Defaults to the parent directory of the input image.

    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.

            Example:
                co=['interleave=bil']

    nodata (integer): the desired NoData-value to be set.
    """

    gdal.AllRegister()
    driver = gdal.GetDriverByName(of)

    ds = gdal.Open(image, GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    if dataBand == None:
        band = ds.GetRasterBand(1)
    else:
        band = ds.GetRasterBand(dataBand)

    data = band.ReadAsArray(0, 0, cols, rows)
    # search for the desired values to be set to 1, set all others 0, making use
    # of the 'eval'-function to concatenate all desired values to a single
    # 'or'.statement for numpy (if a list of values is given instead of a range):
    val_strings = []
    if valRange == True:
        mask = np.where(((data >= values[0]) & (data <= values[1])), 1, 0)
    else:
        for i in xrange(len(values)):
            val_strings.append(string.join(['(data == ', str(values[i]), ')'], sep=''))
        exp = 'np.where((' + string.join([v for v in val_strings], sep=' | ') + '), 1, 0)'
        mask = eval(exp)
    # clean RAM:
    data = None
    band = None
    # create output name:
    if outName == None:
        if outPath == None:
            outname = string.join([os.path.splitext(image)[0], '_mask', \
                                   os.path.splitext(image)[1]], sep='')
        else:
            outname = os.path.join(outPath, \
                                   string.join([os.path.splitext(image)[0], '_mask', \
                                                os.path.splitext(image)[1]], sep=''))
    else:
        if outPath == None:
            outname = os.path.join(os.path.dirname(image), outName)
        else:
            outname = os.path.join(outPath, outName)
    # create output file (with GDAL data type 1 (Byte)):
    if co == None:
        ds_out = driver.Create(outname, cols, rows, 1, 1)
    else:
        ds_out = driver.Create(outname, cols, rows, 1, 1, co)

    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())
    b_out = ds_out.GetRasterBand(1)
    b_out.WriteArray(mask)

    if nodata != None:
        b_out.SetNoDataValue(nodata)

    b_out = None
    ds_out = None
    ds = None


##################
### APPLY MASK ###
##################

def apply_mask(image, maskImage, outName, outPath=None, of='Gtiff', co=None, keepWarp=False):
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

    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.

    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.

            Example:
                co=['interleave=bil']
    keepWarp (boolean): if image and maskImage have different projection, 
            resolution or extent, the mask image will be warped using gdalwarp.
            If keepWarp is True, this warped mask image will not be deleted.
            Defaults to False (will be deleted).
    """

    # check if outfile exists and delete it:
    path = os.path.dirname(image)

    if outPath == None:
        pass
    else:
        path = outPath

    if outName in os.listdir(path):
        print 'Outfile already exists, will be overwritten!'
        os.remove(os.path.join(path, outName))

    gdal.AllRegister()

    driver = gdal.GetDriverByName(of)

    # get information of input raster
    ds = gdal.Open(image, GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    img_proj = ds.GetProjection()
    img_geo = ds.GetGeoTransform()

    # get information of mask
    mask_ds = gdal.Open(maskImage, GA_ReadOnly)
    mask_proj = mask_ds.GetProjection()
    mask_geo = mask_ds.GetGeoTransform()

    # check if inout image and mask share the same projection, resolution and extent
    if img_proj == mask_proj and img_geo == mask_geo:
        pass
    else:
        mask_ds = None
        # warp mask to match input image
        print 'Mask image does not match input image. Transforming mask now...'
        # get bounding box of input image
        minX = img_geo[0]
        maxY = img_geo[3]
        pixSizeX = img_geo[1]
        pixSizeY = img_geo[5]
        maxX = minX + (cols * pixSizeX)
        minY = maxY + (rows * pixSizeY)
        ## set up gdalwarp command
        tempfile = os.path.join(path, os.path.splitext(maskImage)[0] + '_warped' + os.path.splitext(maskImage)[1])
        if os._exists(tempfile):
            os.remove(tempfile)
        of = '-of GTiff'
        bb = '-te %s %s %s %s '%(minX, minY, maxX, maxY)
        res = '-tr %s %s '%(pixSizeX, pixSizeY)
        epsg = int(img_proj.split('''AUTHORITY["EPSG","''')[-1].strip('''"]]'''))
        proj = ''' -t_srs epsg:%s ''' %(epsg)
        warpcmd = string.join(['gdalwarp', of, bb, res, proj, maskImage, tempfile], sep=' ')
        # execute
        os.system(warpcmd)
        # open new file
        maskImage = tempfile
        mask_ds = gdal.Open(maskImage, GA_ReadOnly)

    # open mask image:
    maskBand = mask_ds.GetRasterBand(1)
    mask = maskBand.ReadAsArray(0, 0, mask_ds.RasterXSize, mask_ds.RasterYSize)
    mask_ds = None

    # create (empty) output image:
    if co == None:
        ds_out = driver.Create(os.path.join(path, outName), \
                               ds.RasterXSize, ds.RasterYSize, bands, \
                               ds.GetRasterBand(1).DataType)
    else:
        ds_out = driver.Create(os.path.join(path, outName), \
                                ds.RasterXSize, ds.RasterYSize, bands, \
                                ds.GetRasterBand(1).DataType, co)

    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())
    ds_out.SetMetadata(ds.GetMetadata())

    # apply mask to all bands:
    for b in xrange(1, bands + 1):
        band = ds.GetRasterBand(b)
        data = band.ReadAsArray(0, 0, cols, rows)
        data_out = mask * data
        # write masked band:
        b_out = ds_out.GetRasterBand(b)
        b_out.WriteArray(data_out)

        b_out = None

        try:
            pr.progress(b, xrange(1, bands + 1))
        except:
            pass

    # clean up
    ds_out = None
    ds = None
    if keepWarp == False:
        os.remove(tempfile)


############################
### COMBINE MASKS TO ONE ###
############################

def combine_masks(masks, outName, outPath=None, of='GTiff', co=None):
    """
    Apply a mask to a (multiband) image. The mask will be multiplied with the 
    input image. Both images have to cover the same area, but may differ in 
    resolution.

    Use:

    masks (list): the image masks (full paths and file extensions).

    outName (string): the name of the output file (with file extension).

    outPath (string): the directory to which the output file will be written. 
            Defaults to the parent directory of the first mask image.

    of (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.

    co (list): a list of strings, containing advanced raster creation 
            options such as band interleave.

            Example:
                co=['interleave=bil']
    """

    # check if at least two masks are given
    if len(masks) < 2:
        print 'ERROR: You have to provide two images at least!'
        return

    gdal.AllRegister()
    driver = gdal.GetDriverByName(of)

    ds = gdal.Open(masks[0], GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    data = ds.ReadAsArray(0, 0, cols, rows)

    # create initial output image
    if outPath == None:
        path = os.path.dirname(masks[0])
    else:
        path = outPath

    outFile = os.path.join(path, outName)

    if co == None:
        ds_out = driver.Create(outFile, cols, rows, 1, 1)
    else:
        ds_out = driver.Create(outFile, cols, rows, 1, 1, co)

    # set projection and geotransform
    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())

    for mask in xrange(1, len(masks)):
        m = gdal.Open(masks[mask], GA_ReadOnly)
        mData = m.ReadAsArray(0, 0, cols, rows)

        data = data * mData

    # write final array to file
    b_out = ds_out.GetRasterBand(1)
    b_out.WriteArray(data)

    # clean up
    b_out = None
    ds_out = None
    ds = None
