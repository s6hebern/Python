# -*- coding: utf-8 -*-

"""
    Converting hdf format (used by e.g. USGS to distribute MODIS images) to 
    other image format.
    
    Use:
    
    ----------------------------------------------------------------------------
    
    get_subdataasets: function to get the layer names of the hdf file. Takes the
            hdf file (with full path and file extension) as an argument. If 
            'consoleOut' is set 'True', all layer names will be listed in the 
            console.
            
    ----------------------------------------------------------------------------

    MAIN FUNCTION:
    
    hdf: the hdf file (full path and file extension).
    
    hdfLayer: the desired layer of the hdf file. Layer names can be obtained 
            using the 'get_subdatasets' function, which takes the hdf file 
            (again with full path and file extension) as input argument.
    
    outPath: the path to the desired output directory. If not specified, the 
            directory from the input hdf will be used.
    
    outName: the desired name of the output file (WITHOUT path and file 
            extension). If not specified, the name of the input hdf file will be
            used (since MODIS file names contain '.', they will be substituted 
            by '_').
            
    outFormat:  the desired format of the output file as provided by the GDAL 
            raster formats (see: http://www.gdal.org/formats_list.html). If not
            specified, 'GTiFF' will be used.
            
    outFileExtension: the file extension of the output file (ENVI format has ""). 
            If not specified, '.tif' will be used.
"""

import sys
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import gdal_array
import os
import numpy

# define function for getting the hdf layer-names:
def get_subdatasets(dataset, consoleOut=False):
    source = gdal.Open(dataset, GA_ReadOnly)
    sdsdict = source.GetMetadata('SUBDATASETS')
    if consoleOut == True:
        number = 0
        print 'Subdatasets of', os.path.split(dataset)[1], ':'
        for k in sdsdict.keys():
            if '_NAME' in k:
                number += 1
                print number, ':', sdsdict[k]
    source = None
    return [sdsdict[k] for k in sdsdict.keys() if '_NAME' in k]

# main function:    
def hdf_to_other(hdf, hdfLayer, outPath=None, outName=None, outFormat='GTiff', \
                outFileExtension='.tif'):
     
    # open hdf:
    source = gdal.Open(hdf, GA_ReadOnly)
    # get subdatasets (hdf layers):
    layers = get_subdatasets(source)
    # search for the index of the target layer:
    for i in xrange(len(layers)):
        if layers[i].__contains__(hdfLayer):
            lyrIndex = i
            
    source = None
    
    # open target layer (still in hdf-format)
    lyr = gdal.Open(layers[lyrIndex], GA_ReadOnly)
    band = lyr.GetRasterBand(1)
    
    # convert data type from gdal-type to numpy-type:
    bandType = band.DataType
    numpyBandType = gdal_array.GDALTypeCodeToNumericTypeCode(bandType)
    
    # create new file:
    driver = gdal.GetDriverByName(outFormat)
    # path and name of output file set by default:
    if outPath == None and outName == None:
        out_raster = driver.Create((hdf.replace('.', '_') + '_' + hdfLayer + \
                                        outFileExtension), \
                                    lyr.RasterXSize, lyr.RasterYSize, 1, \
                                    band.DataType)
    # path of output file set by default, name set as requested by user:
    elif outPath == None and outName != None:
        out_raster = driver.Create(os.path.join(os.path.split(hdf)[0], \
                                        (outName + outFileExtension)), \
                                    lyr.RasterXSize, lyr.RasterYSize, 1, \
                                    band.DataType)
    # path of output file set as requested by user, name set by default:
    elif outPath != None and outName == None:
        out_raster = driver.Create(os.path.join(outPath, \
                                        (os.path.split(hdf)[1].replace('.', '_') \
                                    + '_' + hdfLayer + outFileExtension)), \
                                    lyr.RasterXSize, lyr.RasterYSize, 1, \
                                    band.DataType)
    # path and name of output file set as requested by user:
    elif outPath != None and outName != None:
        out_raster = driver.Create(os.path.join(outPath, (outName + \
                                        outFileExtension)), \
                                    lyr.RasterXSize, lyr.RasterYSize, 1, \
                                    band.DataType)
    # set projection
    out_raster.SetProjection(lyr.GetProjection())
    out_raster.SetGeoTransform(lyr.GetGeoTransform())
    
    band = lyr.GetRasterBand(1).ReadAsArray()
    
    #- write output:
    out_band = out_raster.GetRasterBand(1)
    out_band.WriteArray(band)
    
    lyr = None
    out_raster = None
