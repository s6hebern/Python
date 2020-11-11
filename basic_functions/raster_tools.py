import os
import sys
import warnings
import numpy as np
import skimage.io as io
import subprocess as sub
from tqdm import tqdm
from osgeo import gdal, gdalconst, gdal_array, osr
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
from skimage.morphology import disk
from skimage.filters import rank
from basic_functions.call_cmd import run_cmd


"""
------
NOTES:
------
Geotransform definition: (x_min, pixel_size, 0, y_max, 0, -pixel_size)
"""


def get_raster_properties(ds_name):
    # type: (str) -> (int, int, int, gdal.Band.DataType, str, tuple)
    """
    Extract the typical raster properties columns, rows, number of bands, data type (GDAL type),
    projection and geotransform object.

    :param ds_name: Input raster
    :return: Raster properties (cols, rows, bandnum, dtype, proj, geotrans)
    """
    ds = gdal.Open(ds_name, gdal.GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bandnum = ds.RasterCount
    dtype = ds.GetRasterBand(1).DataType
    proj = ds.GetProjection()
    geotrans = ds.GetGeoTransform()
    ds = None
    return cols, rows, bandnum, dtype, proj, geotrans


def create_ds(ds_name, cols, rows, bands, dtype, of='GTiff', co=None, overwrite=True):
    # type: (str, int, int, int, gdal.Band.DataType, str, list, bool) -> gdal.Dataset
    """
    Create a raster dataset.

    :param ds_name: Desired filename.
    :param cols: Number of columns.
    :param rows: Number of rows.
    :param bands: Number of bands.
    :param dtype: GDAL DataType
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param overwrite: Overwrite output file, if it already exists.
    :return: Raster dataset
    """
    if os.path.exists(ds_name) and overwrite is True:
        os.remove(ds_name)
    elif os.path.exists(ds_name) and overwrite is False:
        raise ValueError('Output file {f} already exists and shall not be overwritten! Please '
                         'choose another name or delete it first!'.format(f=ds_name))
    drv = gdal.GetDriverByName(of)
    if co is None:
        ds = drv.Create(ds_name, cols, rows, bands, dtype)
    else:
        ds = drv.Create(ds_name, cols, rows, bands, dtype, co)
    return ds


def delete_ds(ds_name):
    # type: (str) -> None
    """
    Delete a raster file and it's auxiliary files, depending on the data type.

    :param str ds_name: Path to raster file
    :return: --
    """
    ds = gdal.Open(ds_name, gdal.GA_ReadOnly)
    drv = ds.GetDriver()
    ds = None
    drv.Delete(ds_name)
    return


def export_image(output, array, reference, of='GTiff', co=None):
    # type: (str, np.array, str, str, list) -> None
    """
    Export array as image using a reference image to get spatial attributes from.

    :param output: Output image.
    :param array: Input array
    :param reference:
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :return: --
    """
    print('Exporting image to {file}'.format(file=output))
    ds = gdal.Open(reference, gdal.GA_ReadOnly)
    proj = ds.GetProjection()
    geotrans = ds.GetGeoTransform()
    drv = ds.GetDriver()
    ds = None
    if len(array.shape) == 2:
        rows, cols = array.shape
        bands = 1
    else:
        rows, cols, bands = array.shape
    if os.path.exists(output):
        os.remove(output)
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
    return


def get_raster_extent(raster):
    # type: (str) -> (float, float, float, float)
    """
    Extract the corner coordinates of a raster file.

    :param raster: Input raster file.
    :return: Corner coordinates as tuple (xmin, xmax, ymin, ymax).
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


def get_epsg(image):
    # type: (str) -> int
    """
    Extract the EPSG code from a georeferences image.

    :param image: Path to image
    :return: EPSG code
    """
    ds = gdal.Open(image, gdal.GA_ReadOnly)
    proj = ds.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(proj)
    srs.AutoIdentifyEPSG()
    epsg = int(srs.GetAttrValue('AUTHORITY', 1))
    ds = None
    return epsg


def write_blockwise(in_band, out_band, x_size, y_size, blocksize):
    # type: (gdal.Band, gdal.Band, int, int, int) -> None
    """
    Write one band blockwise into another band
    :param in_band: Input raster band
    :param out_band: Output raster band
    :param x_size: Number of columns
    :param y_size: Number of rows
    :param blocksize: Number of rows to read / write at once
    :return: --
    """
    for block in range(0, y_size, blocksize):
        if block + blocksize < y_size:
            num_rows = blocksize
        else:
            num_rows = y_size - block
        data = in_band.ReadAsArray(0, block, x_size, num_rows)
        out_band.WriteArray(data, 0, block)
        print('\t\t{x:.2f}%'.format(x=float(block + num_rows) / y_size * 100))
    return


def set_band_names(raster, band_names):
    # type: (str, tuple) -> None
    """
    Set band names.

    :param raster: Path to raster file
    :param band_names: Tuple of band names as strings
    :return: --
    """
    ds = gdal.Open(raster, gdal.GA_Update)
    for b in tqdm(range(ds.RasterCount)):
        band = ds.GetRasterBand(b + 1)
        band.SetDescription(band_names[b])
    ds.SetMetadata(ds.GetMetadata())
    ds = None


def stack_single_bands(images, outfile, bands=None, of='GTiff', co=None, no_data=0, band_names=None,
                       overwrite=False):
    # type: (tuple, str, tuple, str, list, int or float, tuple, bool) -> None
    """
    Create a layerstack from the given images. They have to share the same spatial reference system,
     data type and dimensions.

    :param images: Input images. Will be stacked in the given order.
    :param outfile: Output image.
    :param bands: The desired band numbers of the input images which shall be used for stacking. By
            this, single bands from multiband-images can be used. Defaults to "None", which means
            that the first band will be used. If more than one band from the same multiband-image
            shall be used, the filename must be given again in the "images" list.
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param no_data: NoData-value, given as int or float (depending on the data type of the
            images). Defaults to the NoData-value of the first input image.
    :param band_names: Band names for the output file, given as strings. Defaults to the names of the
            input files.
    :param bool overwrite: Overwrite output file in case it already exists.
    :return: --
    """
    if os.path.exists(outfile) and overwrite is True:
        delete_ds(outfile)
    elif os.path.exists(outfile) and overwrite is False:
        raise IOError('File {f} already exists! To overwrite, use "overwrite=True"!'.format(
            f=outfile))
    print('Stacking {n} images to {s} ...'.format(n=len(images), s=outfile))
    ds = gdal.Open(images[0], gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    dtype = band.DataType
    if no_data is None:
        no_data = band.GetNoDataValue()
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
        print('\t... band {n} ...'.format(n=i + 1))
        ds = gdal.Open(name, gdal.GA_ReadOnly)
        if bands is None:
            band = ds.GetRasterBand(1)
        else:
            band = ds.GetRasterBand(bands[band_index-1])
        dtype = band.DataType
        data = band.ReadAsArray()
        band_out = ds_out.GetRasterBand(band_index)
        # create new band names (either from original image or from user input):
        if not band_names:
            band_out.SetDescription(band.GetDescription())
        else:
            band_out.SetDescription(band_names[band_index - 1])
        band_out.SetNoDataValue(no_data)
        band_out.WriteArray(data, 0, 0)
        band_index += 1
        band = None
        ds = None
    ds_out = None
    print('Done!')
    return


def stack_images(images, outfile, of='GTiff', co=None, no_data=0, overwrite=False):
    # type: (tuple, str, str, list, int or float, bool) -> None
    """
    Create a layerstack from the given images. They have to share the same spatial reference system,
     data type and dimensions.

    :param images: Input images. Will be stacked in the given order.
    :param outfile: Output image.
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param no_data: NoData-value, given as int or float (depending on the data type of the images).
            Defaults to the NoData-value of the first input image.
    :param overwrite: Overwrite output file in case it already exists.
    :return: --
    """
    if os.path.exists(outfile) and overwrite is True:
        delete_ds(outfile)
    elif os.path.exists(outfile) and overwrite is False:
        raise IOError('File {f} already exists! To overwrite, use "overwrite=True"!'.format(
            f=outfile))
    print('Stacking {n} images to {s} ...'.format(n=len(images), s=outfile))
    cols, rows, __bandnum, dtype, proj, geotrans = get_raster_properties(images[0])
    ds = gdal.Open(images[0], gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    if no_data is None:
        nodata = band.GetNoDataValue()
    else:
        nodata = no_data
    band = None
    ds = None
    total_band_count = 0
    for i in images:
        ds = gdal.Open(i, gdal.GA_ReadOnly)
        total_band_count += ds.RasterCount
        ds = None
    ds_out = create_ds(outfile, cols, rows, total_band_count, dtype, of, co, overwrite)
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(geotrans)
    # loop through all files and stack them:
    band_index = 1
    for i, name in enumerate(images):
        print('\t... Processing {img}'.format(img=name))
        ds = gdal.Open(name, gdal.GA_ReadOnly)
        for b in range(1, ds.RasterCount + 1):
            print('\t\t... band {b}'.format(b=b))
            band = ds.GetRasterBand(b)
            data = band.ReadAsArray()
            band_out = ds_out.GetRasterBand(band_index)
            # create new band names (either from original image or from user input):
            band_out.SetDescription(band.GetDescription())
            band_out.SetNoDataValue(nodata)
            band_out.WriteArray(data, 0, 0)
            band_index += 1
            band = None
        ds = None
    ds_out = None
    print('Done!')
    return


def apply_mask(image, mask, outfile, bands=None, of='GTiff', co=None, no_data=0, overwrite=False):
    # type: (str, str, str, tuple, str, list, int or float, bool) -> None
    """
    Apply a mask containing 0s and 1s to a (multiband) image.

    :param image: Input image
    :param mask: Mask image, containing 0s for areas that shall be masked out and 1s for areas to
            be kept.
    :param outfile: Output image.
    :param bands: The desired band numbers of the input images which shall be used for stacking. By
            this, single bands from multiband-images can be used. Defaults to "None", which means
            that the first band will be used. If more than one band from the same multiband-image
            shall be used, the filename must be given again in the "images" list.
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param no_data: NoData-value, given as int or float (depending on the data type of the images).
            Defaults to the NoData-value of the first input image. <br>
            Example: co=['compress=lzw']
    :param overwrite: Overwrite output file, if it already exists.
    :return: --
    """
    ds_img = gdal.Open(image, gdal.GA_ReadOnly)
    xres, yres = (ds_img.GetGeoTransform()[1], abs(ds_img.GetGeoTransform()[-1]))
    epsg_img = get_epsg(image)
    epsg_mask = get_epsg(mask)
    if epsg_img != epsg_mask:
        print('Image and mask do not share the same coordinate system! Warping mask to EPSG '
              '{e}'.format(e=epsg_img))
        xmin, xmax, ymin, ymax = get_raster_extent(image)
        temp = mask.replace(os.path.splitext(mask)[1], '__WARPED__' + os.path.splitext(mask)[1])
        if os.path.exists(temp):
            delete_ds(temp)
        cmd = ['gdalwarp', '-of', 'GTiff', '-t_srs', 'epsg:{e}'.format(e=epsg_img), '-te',
               str(xmin), str(ymin), str(xmax), str(ymax)]
        cmd += ['-tr',  str(xres), str(yres), mask, temp]
        run_cmd(cmd)
        mask = temp
    ds_mask = gdal.Open(mask, gdal.GA_ReadOnly)
    if (ds_img.RasterXSize, ds_img.RasterYSize) != (ds_mask.RasterXSize, ds_mask.RasterYSize):
        raise AttributeError('Image and mask have different numbers of columns and rows! Please '
                             'adjust and try again!')
    if not bands:
        bands = range(1, ds_img.RasterCount + 1)
    if not no_data:
        no_data = ds_img.GetRasterBand(1).GetNoDataValue()
    ds_out = create_ds(outfile, ds_img.RasterXSize, ds_img.RasterYSize, len(bands),
                       ds_img.GetRasterBand(1).DataType, of, co, overwrite)
    ds_out.SetProjection(ds_img.GetProjection())
    ds_out.SetGeoTransform(ds_img.GetGeoTransform())
    ds_out.SetMetadata(ds_img.GetMetadata())
    data_mask = ds_mask.GetRasterBand(1).ReadAsArray()
    if float(np.min(data_mask)) != 0.0:
        warnings.warn('Minimum value of mask is not 0, but {v}! Setting it to 0!'.format(
            v=np.min(data_mask)))
        data_mask[data_mask == np.min(data_mask)] = 0
    print('Masking band ...')
    for i, b in enumerate(bands):
        print('\t...', b)
        data_img = ds_img.GetRasterBand(b).ReadAsArray()
        data = data_img * data_mask
        band_out = ds_out.GetRasterBand(i + 1)
        band_out.WriteArray(data)
        band_out.SetNoDataValue(no_data)
        band_out = None
    ds_mask = None
    ds_img = None
    print('Done!')
    return


def raster_calculator(image_a, image_b, mode, output, band_a=1, band_b=1, of='GTiff', co=None,
                      no_data_a=None, no_data_b=None, overwrite=False):
    # type: (str, str, str, str, int, int, str, list, int or float, int or float, bool) -> None
    """
    Perform a basic bandwise mathematical operation on two images

    :param image_a: Input image a
    :param image_b: Input image b
    :param mode: Calculation mode. One of ('add', 'subtract', 'multiply' or 'divide') or,
            alternatively, one of ('a', 's', 'm', 'd').
    :param output: Output image
    :param band_a: Band number of image a which will participate in the calculation
    :param band_b: Band number of image b which will participate in the calculation
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param no_data_a: NoData-value of image a, given as int or float (depending on the data type of
            the images).
    :param no_data_b: NoData-value of image b, given as int or float (depending on the data type of
            the images).
    :param overwrite: Overwrite output file, if it already exists.
    :return: --
    """
    if os.path.exists(output) and overwrite is True:
        print('Output {f} already exists and will be overwritten!'.format(f=output))
        delete_ds(output)
    elif os.path.exists(output) and overwrite is True:
        print('Output {f} already exists and shall not be overwritten!'.format(f=output))
        sys.exit(1)
    drv = gdal.GetDriverByName(of)
    print('Reading data ...')
    ds_a = gdal.Open(image_a, gdal.GA_ReadOnly)
    ds_b = gdal.Open(image_b, gdal.GA_ReadOnly)
    data_a = ds_a.GetRasterBand(band_a).ReadAsArray()
    data_b = ds_b.GetRasterBand(band_b).ReadAsArray()
    if no_data_a:
        data_a = np.ma.masked_equal(data_a, no_data_a)
    if no_data_b:
        data_b = np.ma.masked_equal(data_b, no_data_b)
    if co:
        ds_out = drv.Create(output, ds_a.RasterXSize, ds_a.RasterYSize, 1, ds_a.GetRasterBand(band_a).DataType)
    else:
        ds_out = drv.Create(output, ds_a.RasterXSize, ds_a.RasterYSize, 1, ds_a.GetRasterBand(band_a).DataType, co)
    ds_out.SetProjection(ds_a.GetProjection())
    ds_out.SetGeoTransform(ds_a.GetGeoTransform())
    print('Calculating ...')
    if mode in ('add', 'a'):
        data_out = np.add(data_a, data_b)
    elif mode in ('subtract', 's'):
        data_out = np.subtract(data_a, data_b)
    elif mode in ('multiply', 'm'):
        data_out = np.multiply(data_a, data_b)
    elif mode in ('divide', 'd'):
        data_out = np.divide(data_a, data_b)
    else:
        raise ValueError('Error: mode must be one of "add" (or "a"), "subtract" (or "s"), '
                         '"multiply" (or "m") or "divide" (or "d")!')
    print('Writing output ...')
    b_out = ds_out.GetRasterBand(1)
    b_out.WriteArray(data_out)
    b_out = None
    ds_out = None
    ds_b = None
    ds_a = None
    print('Done!')
    return


def calc_raster_stat(image, output, mode='mean', of='GTiff', co=None, no_data=None):
    # type: (str, str, str, str, list, int or float) -> None
    """
    Calculate as statistical value per pixel over all bands contained in the input image and write
    that statistic to a new file.

    :param image: Input image
    :param output: Output image
    :param mode: Statistic to calculate. Possible values are: <br>
            'min', 'max', 'mean', 'med', 'sum', 'std', 'all'
    :param of: the desired format of the output file as provided by the GDAL raster formats
            (see: http://www.gdal.org/formats_list.html).
    :param co: Advanced raster creation options such as band interleave or compression. <br>
            Example: co=['compress=lzw']
    :param no_data: Nodata value, that will be ignored for calculation. Has to be the same in all
            bands.
    :return: --
    """
    print('Reading input file ...')
    ds = gdal.Open(image, gdal.GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    proj = ds.GetProjection()
    geotrans = ds.GetGeoTransform()
    dt = ds.GetRasterBand(1).DataType
    data = ds.GetRasterBand(1).ReadAsArray()
    for b in range(2, ds.RasterCount + 1):
        data = np.dstack((data, ds.GetRasterBand(b).ReadAsArray()))
        if no_data:
            data = np.ma.masked_equal(data, no_data)
    ds = None
    # calculate desired statistic and write to output file
    if mode == 'all':
        modes = ['min', 'max', 'mean', 'med', 'sum', 'std']
        out_bands = len(modes)
    else:
        out_bands = 1
    ds_out = create_ds(output, cols, rows, out_bands, dt, of, co, overwrite=True)
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(geotrans)
    print('Calculating statistic(s) ...')
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
    print('Writing output file ...')
    if out_bands == 1:
        if no_data:
            stat = np.ma.filled(stat, no_data)
        ds_out.GetRasterBand(1).WriteArray(stat)
    else:
        for b in range(out_bands):
            print('\t ... band {n} ...'.format(n=b + 1))
            if no_data:
                stat = np.ma.filled(stats[b], no_data)
            else:
                stat = stats[b]
            ds_out.GetRasterBand(b + 1).WriteArray(stat)
    ds_out = None
    print('Done!')
    return


def local_hist_equalization(image, radius, output):
    # type: (str, int, str) -> None
    """
    Make a local histogram stretch using a moving window.

    :param image: Input image.
    :param radius: Window radius. 1 for a 3x3 window, 2 for 5x5, ...
    :param output: Output image (will be the same format and data type as the input image).
    :return: --
    """
    ds = gdal.Open(image, gdal.GA_ReadOnly)
    drv = ds.GetDriver()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    if os.path.exists(output):
        delete_ds(output)
    out_ds = drv.Create(output, cols, rows, bands, ds.GetRasterBand(1).DataType)
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    if not ds.GetProjection():
        warnings.warn('Warning: Input image seems to have no geo-information! Output image will not'
                      ' be geo-referenced!')
    print('Applying local histogram stretch to image {img}, containing {n} bands'.format(
        img=image, n=bands))
    print('Working on band')
    for b in range(bands):
        print('\t...', b + 1)
        data = ds.GetRasterBand(b + 1).ReadAsArray()
        stretched = rank.equalize(data, selem=disk(radius))
        out_ds.GetRasterBand(b + 1).WriteArray(stretched)
    out_ds = None
    ds = None
    return


def calculate_pc(ds_name, export=None, co=None):
    # type: (str, str, list) -> np.array
    """
    Perform a principal components transformation on an input image.

    :param ds_name: Path to input image.
    :param export: Path to output image, default is None (image will not be saved)
    :param co: Advanced raster creation options such as band interleave or compression. <br<>
            Example: co=['compress=lzw']
    :return: Principal Components of the input image.
    """
    print('Retrieving principal components...')
    img_ds = io.imread(ds_name)
    img = np.array(img_ds, dtype='float64')
    if True in np.isnan(img) or True in np.isinf(img):
        warnings.warn('NaN or Inf detected! Converting to 0 and large number internally!!')
        img = np.nan_to_num(img)
    pca = PCA()
    # transform image to 2-D and calculate PCs
    img_trans = img.reshape(-1, img.shape[-1])
    img_pc = pca.fit_transform(scale(img_trans))
    # transform back
    pc = img_pc.reshape(img.shape)
    if export:
        export_image(export, pc, ds_name, co=co)
    print('Done!')
    return pc


def stretch_greyvalues(array, newmin=0, newmax=255):
    # type: (np.array, int or float, int or float) -> np.array
    """
    Stretch values within an array to new min / max values

    :param array: Input array
    :param newmin: New minimum value
    :param newmax: New maximum value
    :return: Stretched greyvalues
    """
    array = array.astype(np.float32)
    minval = np.nanmin(array)
    maxval = np.nanmax(array)
    newarray = np.zeros_like(array)
    delta = maxval-minval
    if delta > 0:
        np.divide(np.subtract(array, minval), delta, out=array)
        np.multiply(np.multiply(array, np.greater(array, newmin)), newmax, out=array)
    newarray[np.greater(array, newmax)] = newmax
    return array


def match_rasters(reference, warp, output, of='GTiff', co=None, overwrite=True):
    # type: (str, str, str, str, list, bool) -> object
    """
    Map a raster to the projection, extent and resolution of a reference raster

    :param reference: Path to reference image that holds the target projection and extent
    :param warp: Path to the image to be mapped to the reference image
    :param output: Path to the output image
    :param of: Output format as defined at http://www.gdal.org/formats_list.html
    :param co: Advanced raster creation options such as band interleave or compression. <br<>
            Example: co=['compress=lzw']
    :param overwrite: Overwrite output file if it already exists
    :return: --
    """
    if os.path.exists(output) and overwrite is True:
        delete_ds(output)
    elif os.path.exists(output) and overwrite is False:
        raise IOError('File {f} already exists! To overwrite, use "overwrite=True"!'.format(f=output))
    # read reference raster
    print('Reading reference raster {f}'.format(f=reference))
    ref_ds = gdal.Open(reference, gdal.GA_ReadOnly)
    ref_geotrans = ref_ds.GetGeoTransform()
    ref_proj = ref_ds.GetProjection()
    ref_cols = ref_ds.RasterXSize
    ref_rows = ref_ds.RasterYSize
    ref_ds = None
    # read warp raster
    print('Reading source raster {f}'.format(f=warp))
    warp_ds = gdal.Open(warp, gdal.GA_ReadOnly)
    warp_proj = warp_ds.GetProjection()
    warp_band_num = warp_ds.RasterCount
    warp_dtype = warp_ds.GetRasterBand(1).DataType
    # create output file
    drv = gdal.GetDriverByName(of)
    out_ds = create_ds(output, ref_cols, ref_rows, warp_band_num, warp_dtype, of, co, overwrite)
    out_ds.SetGeoTransform(ref_geotrans)
    out_ds.SetProjection(ref_proj)
    # project raster
    print('Matching rasters and writing output to {f}'.format(f=output))
    gdal.ReprojectImage(warp_ds, out_ds, warp_proj, ref_proj, gdalconst.GRA_NearestNeighbour)
    warp_ds = None
    out_ds = None
    print('Done!')
    return True
