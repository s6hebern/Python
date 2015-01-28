# -*- coding: utf-8 -*-

def raster_layerstack(path, outName, outPath=None, outFormat='GTiff', noData=0, dataType=None, createOptions=None, bandNames=None, searchString=None):
    
    """
    Create a layerstack from all files within a directory.
    
    Use:
    
    path (string): the directory containing the single raster files.
    
    outName (string): the name of the output file.
    
    outPath (string): the directory to which the output file will be written. 
            Defaults to the directory given in 'path'.
    
    outFormat (string): the desired format of the output file as provided by the 
            GDAL raster formats (see: http://www.gdal.org/formats_list.html). 
            Defaults to 'GTiFF'.
    
    noData (int / float): the no-data value to be set. Defaults to the no-data 
            value of the first input file.
    
    dataType (int): the desired data type of the output image, as provided by
            the GDAL data types (http://www.gdal.org/gdal_8h.html under 
            'Enumerations'). Defaults to the data type of the input images.
    
    createOptions (list): a list of strings, containing advanced raster creation 
            options such as band interleave.
            
            Example:
                createOptions=['interleave=bil']
                
    bandNames (list): a list of band names for the output file. Defaults to the
            names of the input files.
            
    searchString (string): a combination of characters which all input files 
            must have in common to be used for the layerstack (e.g. file 
            extensions). May be useful, if 'path' contains also other files 
            which shall or can not be used by this function.
    """    

    import os
    import sys
    import string
    from osgeo import gdal
    from osgeo.gdalconst import *
    
    try:
        import module_progress_bar as pr
    except:
        pass

    # check if outfile exists and delete it:
    if outPath == None:
        if outName in os.listdir(path):
            print 'Outfile already exists, will be overwritten!'
            os.remove(os.path.join(path, outName))
    else:
        if outName in os.listdir(outPath):
            print 'Outfile already exists, will be overwritten!'
            os.remove(os.path.join(outPath, outName))
        
    gdal.AllRegister()
    # list all files which shall be stacked:
    files = os.listdir(path)
    if searchString != None:
        files = [item for item in files if item.__contains__(searchString)]
    files.sort()
    # get basic information and create output raster:
    ds = gdal.Open(os.path.join(path, files[0]), GA_ReadOnly)
    band = ds.GetRasterBand(1)
    if noData == None:
        nodata = band.GetNoDataValue()
    else:
        nodata = noData
    driver = gdal.GetDriverByName(outFormat)
    
    if createOptions != None:
        if outPath == None:
            ds_out = driver.Create(os.path.join(path, outName), ds.RasterXSize, \
                    ds.RasterYSize, len(files), band.DataType, createOptions)
        else:            
            ds_out = driver.Create(os.path.join(outPath, outName), \
                        ds.RasterXSize, ds.RasterYSize, len(files), \
                        band.DataType, createOptions)
    else:
        if outPath == None:
            ds_out = driver.Create(os.path.join(path, outName), \
                        ds.RasterXSize, ds.RasterYSize, len(files), \
                        band.DataType)
        else:
            ds_out = driver.Create(os.path.join(outPath, outName), \
                        ds.RasterXSize, ds.RasterYSize, len(files), \
                        band.DataType)
                               
    band = None
    proj = ds.GetProjection()
    ds_out.SetProjection(proj)
    transform = ds.GetGeoTransform()
    ds_out.SetGeoTransform(transform)
    # set band names:
    bands = []
    bandNum = 1
    if bandNames == None:
        for b in files:
            bands.append(string.join(['Band_', str(bandNum), '= ', b], sep=''))
            bandNum += 1
    else:
        for b in bandNames:
            bands.append(string.join(['Band_', str(bandNum), '= ', b], sep=''))
            bandNum += 1
    
    ds_out.SetMetadata(bands)
    
    ds = None
    # loop through all files and stack them:
    band_index = 1
    for name in files:
        # progress bar:
        try:
            pr.progress(name, files)
        except:
            pass
        
        ds = gdal.Open(os.path.join(path, name), GA_ReadOnly)
        band = ds.GetRasterBand(1)
        if dataType == None:
            dtype = band.DataType
        else:
            dtype = dataType
            
        data = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize,
                               ds.RasterXSize, ds.RasterYSize, dtype)
        band_out = ds_out.GetRasterBand(band_index)
        band_out.SetNoDataValue(nodata)
        band_out.WriteRaster(0, 0, ds.RasterXSize, ds.RasterYSize, data,
                             ds.RasterXSize, ds.RasterYSize, dtype)
        ds = None
        band_index += 1
    
    ds_out = None
