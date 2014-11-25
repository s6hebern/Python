# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 13:53:38 2014

@author: Hendrik
"""

### convert MODIS hdf to other format (many files at once) ###

import sys
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import os
import numpy
import subprocess as sp

path = 'WORKING_DIRECTORY'

targetLyr = 'TARGET_LAYER'
imgFormat = 'OUTPU_FORMAT'

#------------------------------------------------------------------------------#

# define function for getting the hdf layer-names:
def get_subdatasets(dataset):
    sdsdict = dataset.GetMetadata('SUBDATASETS')
    return [sdsdict[k] for k in sdsdict.keys() if '_NAME' in k]

#------------------------------------------------------------------------------#

# create list of all .hdf-files in working directoty:
for files in os.walk(path):
    filelist = files[2]

files = []

for i in filelist:
    if i.__contains__('.hdf'):
        files.append(i)

#------------------------------------------------------------------------------#

counter = 0

# convert from .hdf to ENVI:
for data in files:
    counter += 1
    hdf = data
    # open hdf:
    source = gdal.Open(path + '\\' + hdf, GA_ReadOnly)
    # get subdatasets (hdf layers):
    layers = get_subdatasets(source)
    # search for the index of the target layer:
    for i in range(len(layers)):
        if layers[i].__contains__(targetLyr):
            lyrIndex = i
            
    source = None
    
    # open target layer (still in hdf-format)
    lyr = gdal.Open(layers[lyrIndex], GA_ReadOnly)
    band = lyr.GetRasterBand(1)
    
    # convert data type from gdal-type to numpy-type:
    bandType = band.DataType
    numpyBandType = gdal_array.GDALTypeCodeToNumericTypeCode(bandType)
    
    # create new file (name is created from original hdf name):
    driver = gdal.GetDriverByName(imgFormat)
    out_raster = driver.Create(path + '\\' + targetLyr + '_' + \
                    hdf.replace('.', '_')[9:23] + '.ENDING', \
                    lyr.RasterXSize, lyr.RasterYSize, 1, band.DataType)
    # set projection
    out_raster.SetProjection(lyr.GetProjection())
    out_raster.SetGeoTransform(lyr.GetGeoTransform())
    
    band = lyr.GetRasterBand(1).ReadAsArray()
    
    #- write output:
    out_band = out_raster.GetRasterBand(1)
    out_band.WriteArray(band)
    
    lyr = None
    out_raster = None
    print str(counter) + ' of ' + str(len(files)) + ' processed'

print 'Done!'
