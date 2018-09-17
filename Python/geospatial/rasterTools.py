import os
from osgeo import gdal, gdal_array
import numpy as np
import skimage.io as io
from sklearn.decomposition import PCA
from skimage.morphology import disk
from skimage.filters import rank
import warnings


def getRasterExtent(raster):
    """
    Extract the corner coordinates of a raster file.

    :param str raster: Input raster file.
    :return: Corner coordinates as tuple (xmin, xmax, ymin, ymax).
    :rtype: tuple
    """

    ds = gdal.Open(raster, gdal.GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    geotrans = ds.GetGeoTransform()
    xmin = geotrans[0]
    xmax = xmin + cols * geotrans[1]
    ymax = geotrans[3]
    ymin = ymax + rows * geotrans[5]
    ds = None
    return xmin, xmax, ymin, ymax


def createDS(filename, cols, rows, bands, dtype, of='GTiff', co=None, overwrite=True):
    """
    Create a raster dataset.

    :param str filename: Desired filename.
    :param int cols: Number of columns.
    :param int rows: Number of rows.
    :param int bands: Number of bands.
    :param object dtype: GDAL DataType
    :param str of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param list co: Advanced raster creation options such as band interleave or compression.
            Example: co=['interleave=bil']
    :param bool overwrite: Overwrite output file, if it already exists.
    :return: raster dataset
    :rtype: object
    """

    if os.path.exists(filename) and overwrite is True:
        os.remove(filename)
    elif os.path.exists(filename) and overwrite is False:
        raise ValueError('Output file {f} already exists and shall not be overwritten! Please choose another name or '
                         'delete it first!'.format(f=filename))
    drv = gdal.GetDriverByName(of)
    if co is None:
        ds = drv.Create(filename, cols, rows, bands, dtype)
    else:
        ds = drv.Create(filename, cols, rows, bands, dtype, co)
    return ds


def stackImages(images, outfile, bands=None, of='GTiff', co=None, noData=0, bnames=None):
    """
    Create a layerstack from the given images. They have to share the same spatial reference system, data type and
    dimensions.

    :param list images: Input images. Will be stacked in the given order.
    :param str outfile: Output image.
    :param list bands: The desired band numbers of the input images which shall be used for stacking. By this, single
            bands from multiband-images can be used. Defaults to "None", which means that the first band will be used.
            If more than one band from the same multiband-image shall be used, the filename must be given again in the
            "images" list.
    :param str of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param list co: Advanced raster creation options such as band interleave or compression.
            Example: co=['interleave=bil']
    :param numeric noData: NoData-value, given as int or float (depending on the data type of the images). Defaults to
            the NoData-value of the first input image.
    :param list bnames: Band names for the output file, given as strings. Defaults to the names of the input files.
    :return: --
    """

    print 'Stacking {n} images to {s} ...'.format(n=len(images), s=outfile)
    ds = gdal.Open(images[0], gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    dtype = band.DataType
    if noData is None:
        nodata = band.GetNoDataValue()
    else:
        nodata = noData
    driver = gdal.GetDriverByName(of)
    if co is None:
        ds_out = driver.Create(outfile, cols, rows, len(images), dtype)
    else:
        ds_out = driver.Create(outfile, cols, rows, len(images), dtype, co)
    ds_out.SetProjection(ds.GetProjection())
    ds_out.SetGeoTransform(ds.GetGeoTransform())
    band = None
    ds = None
    # loop through all files and stack them:
    band_index = 1
    for i, name in enumerate(images):
        print '\t... band {n} ...'.format(n=i + 1)
        ds = gdal.Open(name, gdal.GA_ReadOnly)
        if bands is None:
            band = ds.GetRasterBand(1)
        else:
            band = ds.GetRasterBand(bands[band_index-1])
        dtype = band.DataType
        data = band.ReadAsArray()
        band_out = ds_out.GetRasterBand(band_index)
        # create new band names (either from original image or from user input):
        if bnames == None:
            band_out.SetDescription(band.GetDescription())
        else:
            band_out.SetDescription(bnames[band_index - 1])
        band_out.SetNoDataValue(nodata)
        band_out.WriteArray(data, 0, 0)
        band_index += 1
        band = None
        ds = None
    ds_out = None
    print '\tDone!'
    return


def calcRasterStat(image, output, mode='mean', of='GTiff', co=None, nodata=None):
    """
    Calculate as statistical value per pixel over all bands contained in the input image and write that statistic to a
    new file.

    :param str image: Input image
    :param str output: Output image
    :param str mode: Statistic to calculate. Possible values are:
                        'min', 'max', 'mean', 'med', 'sum', 'std', 'all'
    :param str of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param list co: Advanced raster creation options such as band interleave or compression.
            Example: co=['interleave=bil']
    :param numeric nodata: Nodata value, that will be ignored for calculation. Has to be the same in all bands.
    :return: --
    """

    print 'Reading input file ...'
    ds = gdal.Open(image, gdal.GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    proj = ds.GetProjection()
    geotrans = ds.GetGeoTransform()
    dt = ds.GetRasterBand(1).DataType
    data = ds.GetRasterBand(1).ReadAsArray()
    for b in range(2, ds.RasterCount + 1):
        data = np.dstack((data, ds.GetRasterBand(b).ReadAsArray()))
        if nodata:
            data = np.ma.masked_equal(data, nodata)
    ds = None
    # calculate desired statistic and write to output file
    if mode == 'all':
        modes = ['min', 'max', 'mean', 'med', 'sum', 'std']
        out_bands = len(modes)
    else:
        out_bands = 1
    ds_out = createDS(output, cols, rows, out_bands, dt, of, co, overwrite=True)
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(geotrans)
    print 'Calculating statistic(s) ...'
    if mode == 'min':
        stat = np.nanmin(data, -1)
    elif mode == 'max':
        stat = np.nanmax(data, -1)
    elif mode == 'mean':
        stat = np.nanmean(data, -1)
    elif mode == 'med':
        stat = np.nanmedian(data, -1)
    elif mode == 'sum':
        stat = np.nansum(data, -1)
    elif mode == 'std':
        stat = np.nanstd(data, -1)
    elif mode == 'all':
        stats = []
        stats.append = np.nanmin(data, -1)
        stats.append = np.nanmax(data, -1)
        stats.append = np.nanmean(data, -1)
        stats.append = np.nanmedian(data, -1)
        stats.append = np.nansum(data, -1)
        stats.append = np.nanstd(data, -1)
    else:
        raise ValueError('Invalid mode!')
    print 'Writing output file ...'
    if out_bands == 1:
        if nodata:
            stat = np.ma.filled(stat, nodata)
        ds_out.GetRasterBand(1).WriteArray(stat)
    else:
        for b in range(out_bands):
            print '\t ... band {n} ...'.format(n=b + 1)
            if nodata:
                stat = np.ma.filled(stats[b], nodata)
            else:
                stat = stats[b]
            ds_out.GetRasterBand(b + 1).WriteArray(stat)
    ds_out = None
    print 'Done!'
    return True


def localHistEqualization(image, radius, output):
    """
    Make a local histogram stretch using a moving window.

    :param str image: Input image.
    :param int radius: Window radius. 1 for a 3x3 window, 2 for 5x5, ...
    :param str output: Output image (will be the same format and data type as the input image).
    :return: --
    """

    ds = gdal.Open(image, gdal.GA_ReadOnly)
    drv = ds.GetDriver()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    if os.path.exists(output):
        os.remove(output)
    out_ds = drv.Create(output, cols, rows, bands, ds.GetRasterBand(1).DataType)
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    if not ds.GetProjection():
        warnings.warn('Warning: Input image seems to have no geo-information! Output image will not be geo-referenced!')
    print 'Applying local histogram stretch to image {img}, containing {n} bands'.format(img=image, n=bands)
    print 'Working on band'
    for b in range(bands):
        print '\t...', b + 1
        data = ds.GetRasterBand(b + 1).ReadAsArray()
        stretched = rank.equalize(data, selem=disk(radius))
        out_ds.GetRasterBand(b + 1).WriteArray(stretched)
    out_ds = None
    ds = None
    return True


def calculatePC(image, export=None, co=None):
    """
    Perform a principal components transformation on an input image.

    :param str image: Path to input image.
    :param str export: Path to output image, default is None (image will not be saved)
    :param list co: Advanced raster creation options such as band interleave or compression.
            Example: co=['interleave=bil']
    :return: Principal Components of the input image.
    :rtype: array
    """

    print 'Retrieving principal components...'
    img_ds = io.imread(image)
    img = np.array(img_ds, dtype='float32')
    pca = PCA()
    # transform image to 2-D and calculate PCs
    img_trans = img.reshape(-1, img.shape[-1])
    pca.fit(img_trans)
    img_pc = pca.transform(img_trans)
    # transform back
    pc = img_pc.reshape(img.shape)
    if export:
        exportImage(export, pc, image, co)
    print '\tDone!'
    return pc


def exportImage(output, array, reference, of='GTiff', co=None):
    """
    Export array as image using a reference image to get spatial attributes from.

    :param str output: Output image.
    :param array array: Input array
    :param str reference:
    :param str of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param list co: Advanced raster creation options such as band interleave or compression.
            Example: co=['interleave=bil']
    :return: --
    """

    print 'Exporting image to {file}'.format(file=output)
    ds = gdal.Open(reference, gdal.GA_ReadOnly)
    proj = ds.GetProjection()
    geotrans = ds.GetGeoTransform()
    ds = None
    if len(array.shape) == 2:
        rows, cols = array.shape
        bands = 1
    else:
        rows, cols, bands = array.shape
    if os.path.exists(output):
        os.remove(output)
    drv = gdal.GetDriverByName(of)
    dtype = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
    if not co:
        ds = drv.Create(output, cols, rows, bands, dtype)
    else:
        ds = drv.Create(output, cols, rows, bands, dtype, co)
    ds.SetProjection(proj)
    ds.SetGeoTransform(geotrans)
    for b in range(bands):
        ds_band = ds.GetRasterBand(b + 1)
        if bands == 1:
            ds_band.WriteArray(array, 0, 0)
        else:
            ds_band.WriteArray(array[:, :, b], 0, 0)
    ds = None
    return True
