# -*- coding: utf-8 -*-

import os
import sys
import string
import shutil
import math
import re
import time
import datetime
import warnings
import numpy as np
import subprocess as sub
from tqdm import tqdm
from osgeo import ogr, osr, gdal, gdal_array
from optparse import OptionParser, OptionGroup


OGR_TYPES = {int: ogr.OFTInteger,
             float: ogr.OFTReal}


class PolygonSampling(object):
    def __init__(self, argv):
        self._image = None
        self._poly = None
        self._output = None
        self._overwrite = False
        self._radius = 0
        self._mode = 'median'
        self._bands = None
        self._nodata = None
        self._names = None
        self._crs = 'raster'
        print('Running "PolygonSampling"...\n')

    def setup_option_parser(self):
        parser = OptionParser("""
Description:
-----------
Sample a raster dataset within specific segments, indicated by a spatial polygon vector file. The 
tool will pay attention to spatial reference.  Raster attributes will be added as new attributes.

For a full list of supported raster formats, refer to https://www.gdal.org/formats_list.html.
For a full list of supported vector formats, refer to https://gdal.org/ogr_formats.html.

Requirements:
-------------
NumPy (1.10.4 +)

GDAL / OGR installation with Python bindings (OSGeo 1.11.3 +)

GDAL / OGR commands in PATH environment
""", conflict_handler='resolve')
        group = OptionGroup(parser, 'Mandatory options', 'Must be defined')
        group.add_option('-i', '--image', dest='image', type='str',
                         help='Input image to sample (raster format)')
        group.add_option('-p', '--polygons', dest='polygons', type='str',
                         help='Sampling polygons (vector format)')
        parser.add_option_group(group)
        group = OptionGroup(parser, 'Optional arguments', 'Can be defined')
        group.add_option('-m', '--mode', dest='mode', type='str', default='median',
                         help='Statistic to use from within sampling window. One of (median '
                              '(default), mean, min, max, majority, stdv)')
        group.add_option('-b', '--bands', dest='bands', type='str',
                         help='List of exclusive bands to use, separated by comma (no space!). '
                              'Counting starts at 1.')
        group.add_option('-n', '--names', dest='names', type='str',
                         help='Field names for the target attributes. Must not exceed 10 characters'
                              ' and only contain "a-z,A-Z,0-9,_". If a field already exists, its '
                              'values will be overwritten!')
        group.add_option('-c', '--crs', dest='crs', type='str', default='raster',
                         help='Use spatial reference system from input image ("raster"; default) or'
                              ' sampling points ("points") if internal reprojection is necessary.')
        group.add_option('-o', '--output', dest='output', type='str',
                         help='Output file, if desired. If not given, the new attributes will be '
                              'appended to the input dataset. The file extension needs to match the'
                              ' one from the input dataset, since they will be in the same format.')
        group.add_option('', '--overwrite', dest='overwrite', action='store_true',
                         default=False, help='Overwrite output file, if it already exists.')
        group.add_option('', '--nodata', dest='nodata', type='int',
                         help='Additional raster NoData value. It will be ignored for statistical '
                              'calculation in addition to the rasters internal NoData value, which '
                              'is ignored anyway.')
        parser.add_option_group(group)
        return parser

    def check_options(self):
        parser = self.setup_option_parser()
        (options, args) = parser.parse_args()
        self._image = options.image
        if not options.image:
            parser.print_help()
            raise IOError('No input image!')
        self._poly = options.polygons
        if not options.polygons:
            parser.print_help()
            raise IOError('No sampling polygons!')
        self._output = options.output
        self._overwrite = options.overwrite
        if self._output and os.path.exists(self._output) and not self._overwrite:
            parser.print_help()
            raise IOError('Desired output file {f} already exists and shall not be overwritten!'
                          ''.format(f=self._output))
        self._mode = options.mode
        if options.bands:
            try:
                self._bands = options.bands.split(',')
            except:
                parser.print_help()
                raise IOError('Unable to split band indices! Make sure they are separated by comma,'
                              ' but no space!')
        else:
            self._bands = options.bands
        self._nodata = options.nodata
        if options.names:
            try:
                self._names = options.names.split(',')
            except:
                parser.print_help()
                raise IOError('Unable to split attribute names! Make sure they are separated by '
                              'comma, but no space!')
        else:
            self._names = None
        self._crs = options.crs
        return True

    def run(self):
        start = time.time()
        warnings.simplefilter('ignore', FutureWarning)
        self.check_options()
        tmp_dir = os.path.join(os.path.dirname(self._poly), '__tmp')
        for ti in time.localtime():
            tmp_dir += str(ti)
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        print('Checking spatial references...')
        self._poly, self._image = self._match_projection(self._poly, self._image, tmp_dir,
                                                         match=self._crs)
        self._poly = self._reproject_and_cut_shape(self._image, self._poly, tmp_dir)
        cols, rows, bandnum, _dtype, _proj, geotrans = self.get_raster_properties(self._image)
        ds_img = gdal.Open(self._image, gdal.GA_ReadOnly)
        # get band count and band names
        if not self._bands:
            self._bands = [b for b in range(1, bandnum + 1)]
        if not self._names:
            self._names = [bn.split('=')[1] for bn in ds_img.GetMetadata_List() if
                           bn.startswith('Band') and int(bn.split('=')[0].split('_')[1]) in
                           self._bands]
            self._names = [re.sub(r'[^a-zA-Z0-9_]', r'', n) if len(n) <= 10 else
                           re.sub(r'[^a-zA-Z0-9_]', r'', n)[:10] for n in self._names]
            if not self._names:
                self._names = ['band_{b}'.format(b=bn) for bn in self._bands]
        # open vector file
        if self._output:
            print('Creating new output file...')
            ds = ogr.Open(self._poly)
            drv = ds.GetDriver()
            if os.path.exists(self._output) and self._overwrite:
                drv.DeleteDataSource(self._output)
            drv.CopyDataSource(ds, self._output)
            ds = None
            input_polys = self._output
        else:
            input_polys = self._poly
        ds_polys = ogr.Open(input_polys, 1)
        lyr = ds_polys.GetLayer()
        lyr_defn = lyr.GetLayerDefn()
        crs = lyr.GetSpatialRef()
        # check if new attribute names already exist
        fields = [lyr_defn.GetFieldDefn(f).name for f in range(lyr_defn.GetFieldCount())]
        for n in self._names:
            if n in fields:
                warnings.warn('Field {f} already exists! Values will be overwritten!'.format(f=n))
                lyr.DeleteField(fields.index(n))
        # loop over each band
        print('')
        for b, bandnum in enumerate(self._bands):
            print('Working on band {b} of {n}...'.format(b=b+1, n=len(self._bands)))
            band = ds_img.GetRasterBand(int(bandnum))
            no_data = band.GetNoDataValue()
            dtype = gdal_array.GDALTypeCodeToNumericTypeCode(band.DataType)
            # create field
            if not self._mode == 'majority':
                field = ogr.FieldDefn(self._names[b], OGR_TYPES[type(dtype(0).item())])
                field.SetWidth(20)
                field.SetPrecision(8)
            else:
                field = ogr.FieldDefn(self._names[b], ogr.OFTInteger)
                field.SetWidth(10)
            lyr.CreateField(field)
            # loop features
            start = time.time()
            # for f in xrange(len(lyr)):
            for f in tqdm(xrange(len(lyr)), mininterval=1, maxinterval=1, smoothing=0.5,
                          desc='Progress: '):
                tmp_shp = os.path.join(tmp_dir, '__tmp.shp')
                tmp_tif = os.path.join(tmp_dir, '__tmp.tif')
                drv = ogr.GetDriverByName('ESRI Shapefile')
                tmp_ds = drv.CreateDataSource(tmp_shp)
                tmp_lyr = tmp_ds.CreateLayer('tmp', crs, ogr.wkbPolygon)
                tmp_lyr.CreateFeature(lyr.GetFeature(f))
                tmp_lyr = None
                tmp_ds.Destroy()
                self._rasterize_polygon(tmp_shp, self._image, tmp_tif)
                tmp_ulx, tmp_lrx, tmp_lry, tmp_uly = self.get_raster_extent(tmp_tif)
                tmp_ds = gdal.Open(tmp_tif, gdal.GA_ReadOnly)
                poly_mask = tmp_ds.GetRasterBand(1).ReadAsArray()
                tmp_ds = None
                window_index_ulx, window_index_uly = self.geo_to_pixel_coords(tmp_ulx, tmp_uly,
                                                                              geotrans, cols, rows)
                window_index_lrx, window_index_lry = self.geo_to_pixel_coords(tmp_lrx, tmp_lry,
                                                                              geotrans, cols, rows)
                window_cols = window_index_lrx - window_index_ulx
                window_rows = window_index_lry - window_index_uly
                window = band.ReadAsArray(window_index_ulx, window_index_lry, window_cols,
                                          window_rows)
                window = window[np.equal(poly_mask, 1)]
                window = np.ma.masked_equal(window, no_data)
                window = np.ma.masked_equal(window, self._nodata)
                # calculate statistic
                data = self.calculate_stats(window, self._mode, no_data)
                if data == no_data:
                    data = None
                elif not data:
                    data = None
                # set attribute
                feat = lyr.GetFeature(f)
                if data:
                    if type(dtype(0).item()) == float:
                        try:
                            feat.SetField(self._names[b], float(round(data, 8)))
                        except:
                            pass
                    elif type(dtype(0).item()) == int:
                        feat.SetField(self._names[b], int(data))
                    else:
                        print self._names[b], data
                        raise ValueError('Should not happen!')
                else:
                    feat.SetField(self._names[b], data)
                lyr.SetFeature(feat)
                feat.Destroy()
                self.delete_ds(tmp_shp)
                os.remove(tmp_tif)
            band = None
        lyr = None
        ds_polys.Destroy()
        ds_img = None
        self.delete_ds(self._poly)
        shutil.rmtree(tmp_dir)
        print('\nDuration (hh:mm:ss): \t {dur}'.format(dur=datetime.timedelta(seconds=time.time()
                                                                                      - start)))
        return True

    # ----------------------------------------------------------------------- #
    # HELPER FUNCTIONS
    @staticmethod
    def run_cmd(command):
        p = sub.Popen(command, stdout=sub.PIPE, stderr=sub.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print string.join(command)
            print stdout
            print stderr
            sys.exit(1)
        return True

    @staticmethod
    def delete_ds(ds_name):
        ds = ogr.Open(ds_name)
        drv = ds.GetDriver()
        ds.Destroy()
        drv.DeleteDataSource(ds_name)
        return True

    def _match_projection(self, shape, raster, outputdir, match='raster'):
        ds = gdal.Open(raster)
        wkt = ds.GetProjection()
        srs_raster = osr.SpatialReference(wkt=wkt)
        srs_raster.AutoIdentifyEPSG()
        epsg_raster = int(srs_raster.GetAttrValue('AUTHORITY', 1))
        ds = None
        ds = ogr.Open(shape)
        srs_shape = ds.GetLayer().GetSpatialRef()
        srs_shape.AutoIdentifyEPSG()
        epsg_shape = int(srs_shape.GetAttrValue('AUTHORITY', 1))
        ds.Destroy()
        ulx, lrx, lry, uly = self.get_raster_extent(raster)
        if epsg_raster != epsg_shape:
            if match == 'raster':
                print('Reprojecting shape to EPSG:{0}'.format(epsg_raster))
                proj_shape = os.path.join(outputdir, os.path.splitext(os.path.basename(shape))[0]
                                          + '_projected.shp')
                if os.path.exists(proj_shape):
                    self.delete_ds(proj_shape)
                warnings.warn('Need to reproject polygons! New output dataset will be {ds}'.format(
                    ds=proj_shape))
                cmd = ['ogr2ogr', '-overwrite', '-f', 'ESRI Shapefile', '-t_srs', 'EPSG:{e}'.format(
                    e=epsg_raster),
                       '-clipdst', ulx, lry, lrx, uly, proj_shape, shape]
                self.run_cmd([str(i) for i in cmd])
                return proj_shape, raster
            else:
                print('Reprojecting raster to EPSG:{0}'.format(epsg_shape))
                temp_raster = os.path.join(outputdir, os.path.splitext(os.path.basename(raster)[0]
                                                                       + '_projected.tif'))
                cmd = 'gdalwarp -of GTiff -overwrite -te_srs EPSG:{e} {r} {t}'.format(
                    e=epsg_shape, r=raster, t=temp_raster)
                self.run_cmd(cmd)
                return shape, temp_raster
        else:
            print('Polygons and raster have the same projection! No reprojection necessary!')
        return shape, raster

    def _reproject_and_cut_shape(self, raster, shape, outputdir):
        out_shape = os.path.join(outputdir, 'temp_utm.shp')
        if os.path.exists(out_shape):
            self.delete_ds(out_shape)
        # read raster information
        _c, _r, _b, _d, proj, _g = self.get_raster_properties(raster)
        ulx, lrx, lry, uly = self.get_raster_extent(raster)
        ds = ogr.Open(shape)
        proj_shape = ds.GetLayer().GetSpatialRef()
        ds.Destroy()
        proj_shape = str(proj_shape).replace('\n', '').replace(' ', '')
        sr_raster = osr.SpatialReference()
        sr_shape = osr.SpatialReference()
        sr_raster.ImportFromWkt(proj)
        sr_shape.ImportFromWkt(proj_shape)
        sr_raster.AutoIdentifyEPSG()
        sr_shape.AutoIdentifyEPSG()
        epsg_raster = int(sr_raster.GetAttrValue('AUTHORITY', 1))
        epsg_shape = int(sr_shape.GetAttrValue('AUTHORITY', 1))
        cmd = ['ogr2ogr', '-s_srs', 'EPSG:{es}'.format(es=epsg_shape), '-t_srs', 'EPSG:{er}'.format(
            er=epsg_raster),
               '-f', 'ESRI Shapefile', '-skipfailures', '-clipdst', str(ulx), str(lry), str(lrx),
               str(uly), out_shape, shape]
        self.run_cmd(cmd)
        return out_shape

    def _rasterize_polygon(self, polygon, refraster, outraster, outformat='GTiff'):
        ds = gdal.Open(refraster, gdal.GA_ReadOnly)
        geotrans = ds.GetGeoTransform()
        drv = ds.GetDriver()
        ds = None
        if os.path.exists(outraster):
            drv.DeleteDataSource()
        ds = ogr.Open(polygon)
        lyr = ds.GetLayer()
        ulx, lrx, uly, lry = lyr.GetExtent()
        xres, yres = geotrans[1], abs(geotrans[5])
        lyrname = os.path.splitext(os.path.basename(polygon))[0]
        cmd = ['gdal_rasterize', '-burn', '1', '-of', outformat, '-te', ulx, uly, lrx, lry, '-tr',
               xres, yres, '-ot', 'Byte', '-l', lyrname, polygon, outraster]
        self.run_cmd([str(i) for i in cmd])
        return True

    @staticmethod
    def get_raster_properties(raster):
        ds = gdal.Open(raster, gdal.GA_ReadOnly)
        cols = ds.RasterXSize
        rows = ds.RasterYSize
        bandnum = ds.RasterCount
        dtype = ds.GetRasterBand(1).DataType
        proj = ds.GetProjection()
        geotrans = ds.GetGeoTransform()
        ds = None
        return cols, rows, bandnum, dtype, proj, geotrans

    @staticmethod
    def get_raster_extent(raster):
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

    @staticmethod
    def geo_to_pixel_coords(x, y, geotrans, cols, rows):
        ulx = geotrans[0]
        uly = geotrans[3]
        lrx = geotrans[0] + cols * geotrans[1]
        lry = geotrans[3] + rows * geotrans[5]
        if x < ulx or x > lrx or y < lry or y > uly:
            warnings.warn('Coordinate is outside the image!')
        # do the math
        x_pix = int(math.floor((x - ulx) / geotrans[1]))
        y_pix = int(math.floor((uly - y) / -geotrans[5]))
        if x_pix < 0:
            x_pix = 0
        if y_pix < 0:
            y_pix = 0
        return x_pix, y_pix

    @staticmethod
    def calculate_stats(array, mode, nodata=None):
        if array.size == 0:
            data = nodata
        else:
            if nodata:
                array = np.ma.masked_equal(array, nodata)
            if mode == 'median':
                data = np.ma.median(np.ma.masked_invalid(array))
            elif mode == 'mean':
                data = np.ma.mean(np.ma.masked_invalid(array))
            elif mode == 'min':
                data = np.ma.min(np.ma.masked_invalid(array))
            elif mode == 'max':
                data = np.ma.max(np.ma.masked_invalid(array))
            elif mode == 'majority':
                if not array.dtype == 'int':
                    warnings.warn('Mode "majority" only works with integer values! Converting '
                                  'accordingly!')
                data = int(np.bincount(array.astype(int).flatten()).argmax())
            elif mode == 'stdv':
                data = np.ma.std(np.ma.masked_invalid(array))
            else:
                data = None
        return data


# run
if __name__ == '__main__':
    app = PolygonSampling(sys.argv)
    app.setup_option_parser()
    app.check_options()
    app.run()
