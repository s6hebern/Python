import os
from osgeo import gdal, gdalconst


def matchRasters(reference, warp, output, of='GTiff', co=[], overwrite=True):
    # type: (str, str, str, str, list, bool) -> object
    """
    Map a raster to the projection, extent and resolution of a reference raster

    :param str reference: Path to reference image that holds the target projection and extent
    :param str warp: Path to the image to be mapped to the reference image
    :param str output: Path to the output image
    :param str of: Output format as defined at http://www.gdal.org/formats_list.html
    :param list co: Creation options that can be used for raster creation (e.g. ["bigtiff=yes"]). Must be a list of
                    strings.
    :param bool overwrite: Overwrite output file if it already exists
    :return: --
    """

    # read reference raster
    print 'Reading reference raster {f}'.format(f=ref)
    ref_ds = gdal.Open(reference, gdal.GA_ReadOnly)
    ref_geotrans = ref_ds.GetGeoTransform()
    ref_proj = ref_ds.GetProjection()
    ref_cols = ref_ds.RasterXSize
    ref_rows = ref_ds.RasterYSize
    ref_ds = None
    # read warp raster
    print 'Reading source raster {f}'.format(f=warp)
    warp_ds = gdal.Open(warp, gdal.GA_ReadOnly)
    warp_geotrans = warp_ds.GetGeoTransform()
    warp_proj = warp_ds.GetProjection()
    warp_band_num = warp_ds.RasterCount
    warp_dtype = warp_ds.GetRasterBand(1).DataType
    # create output file
    drv = gdal.GetDriverByName(of)
    if os.path.exists(output) and overwrite is True:
        os.remove(output)
    elif os.path.exists(output) and overwrite is False:
        raise IOError('File {f} already exists! To overwrite, use "overwrite=True"!'.format(f=output))
    out_ds = drv.Create(output, ref_cols, ref_rows, warp_band_num, warp_dtype, co)
    out_ds.SetGeoTransform(ref_geotrans)
    out_ds.SetProjection(ref_proj)
    # project raster
    print 'Matching rasters and writing outout to {f}'.format(f=output)
    gdal.ReprojectImage(warp_ds, out_ds, warp_proj, ref_proj, gdalconst.GRA_NearestNeighbour)
    warp_ds = None
    out_ds = None
    print 'Done!'
    return True


if __name__ == '__main__':
    ref = r'c:\working\testing\match\ref.tif'
    warp = r'c:\working\testing\match\src.tif'
    dst = r'c:\working\testing\match\test.tif'
    matchRasters(ref, warp, dst)
