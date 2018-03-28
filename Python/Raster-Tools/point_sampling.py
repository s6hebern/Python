# -*- coding: utf-8 -*-

import os, sys, re, time, datetime, warnings
import numpy as np
import subprocess as sub
from osgeo import ogr, osr, gdal, gdal_array
from optparse import OptionParser, OptionGroup


OGR_TYPES = {int: ogr.OFTInteger,
             float: ogr.OFTReal}


class pointSampling(object):
    """
    Sample a raster dataset at specific coordinates, indicated by a spatial point vector file. The tool will pay
    attention to spatial reference and is able to not only sample the exact pixel for each point, but also a winow
    with given radius around it, where different statistical measures can be calculated.
    """
    def __init__(self, argv):
        print 'Running "pointSampling"...\n'

    def setupOptionParser(self):
        parser = OptionParser("""
Description:
    Sample a raster based on a point vector file. Raster attributes will be added as new attributes.
""", conflict_handler='resolve')
        group = OptionGroup(parser, 'Mandatory options', 'Must be defined')
        group.add_option('-i', '--image', dest='image', type='str', help='Input image to sample (raster format)')
        group.add_option('-p', '--points', dest='points', type='str', help='Sampling points (vector format)')
        parser.add_option_group(group)
        group = OptionGroup(parser, 'Optional arguments', 'Can be defined')
        group.add_option('-r', '--radius', dest='radius', type='int', default=0, help='Sampling radius')
        group.add_option('-m', '--mode', dest='mode', type='str', default='median', help='Statistic to use from within '
                                                                                         'sampling window. One of '
                                                                                         '(median, mean, min, max, '
                                                                                         'majority)')
        group.add_option('-b', '--bands', dest='bands', type='str', default=None, help='List of exclusive bands to '
                                                                                       'use. Counting starts at 1.')
        group.add_option('-d', '--dismiss', dest='dismiss', default=None, help='Raster value to dismiss. It will be '
                                                                               'ignored for statistical calculation.')
        group.add_option('-n', '--names', dest='names', type='str', default=None, help='Field names for the target '
                                                                                       'attributes. Must not exceed 10 '
                                                                                       'characters and only contain '
                                                                                       '"a-z,A-Z,0-9,_". If a field '
                                                                                       'already exists, its values will '
                                                                                       'be overwritten!')
        group.add_option('-c', '--crs', dest='crs', type='str', default='raster', help='Use spatial reference system '
                                                                                       'from input image ("raster"; '
                                                                                       'default) or sampling points '
                                                                                       '("points")')
        parser.add_option_group(group)
        return parser

    def checkOptions(self):
        parser = self.setupOptionParser()
        (options, args) = parser.parse_args()
        self._image = options.image
        if not options.image:
            parser.print_help()
            print 'No input image!'
            sys.exit(1)
        self._points = options.points
        if not options.points:
            parser.print_help()
            print 'No sampling points!'
            sys.exit(1)
        self._radius = int(options.radius)
        self._mode = options.mode
        if options.bands:
            try:
                self._bands = options.bands.split(',')
            except:
                parser.print_help()
                print 'Unable to split band indices! Make sure they are separated by comma, but no space!'
                sys.exit(1)
        else:
            self._bands = options.bands
        self._dismiss = options.dismiss
        if options.names:
            try:
                self._names = options.names.split(',')
            except:
                parser.print_help()
                print 'Unable to split attribute names! Make sure they are separated by comma, but no space!'
                sys.exit(1)
        else:
            self._names = options.names
        self._crs = options.crs
        return True

    def run(self):
        start = time.time()
        warnings.simplefilter('ignore', FutureWarning)
        self.checkOptions()
        print 'Checking spatial references...'
        self._points, self._image = self._matchProjection(self._points, self._image, match=self._crs)
        # get raster information
        ds_img = gdal.Open(self._image, gdal.GA_ReadOnly)
        cols = ds_img.RasterXSize
        rows = ds_img.RasterYSize
        geotrans = ds_img.GetGeoTransform()
        ulx = geotrans[0]
        uly = geotrans[3]
        resolution = geotrans[1]
        # get band count and band names
        if not self._bands:
            self._bands = [b for b in range(1, ds_img.RasterCount + 1)]
        if not self._names:
            self._names = [bn.split('=')[1] for bn in ds_img.GetMetadata_List() if bn.startswith('Band') and
                           int(bn.split('=')[0].split('_')[1]) in self._bands]
            self._names = [re.sub(r'[^a-zA-Z0-9_]', r'', n) if len(n) <= 10 else re.sub(r'[^a-zA-Z0-9_]', r'', n)[:10]
                           for n in self._names]
            if not self._names:
                self._names = ['band_{b}'.format(b=bn) for bn in self._bands]
        # open vector file
        ds_points = ogr.Open(self._points, 1)
        drv = ds_points.GetDriver()
        lyr = ds_points.GetLayer()
        lyr_defn = lyr.GetLayerDefn()
        # check if new attribute names already exist
        fields = [lyr_defn.GetFieldDefn(f).name for f in range(lyr_defn.GetFieldCount())]
        for n in self._names:
            if n in fields:
                warnings.warn('Field {f} already exists! Values will be overwritten!'.format(f=n))
                lyr.DeleteField(fields.index(n))
        # get coordinates
        points = [(p.GetGeometryRef().GetX(), p.GetGeometryRef().GetY()) for p in lyr]
        # loop over each band
        for b, bandnum in enumerate(self._bands):
            band = ds_img.GetRasterBand(bandnum)
            no_data = band.GetNoDataValue()
            dt = gdal_array.GDALTypeCodeToNumericTypeCode(band.DataType)
            # create field
            if not self._mode == 'majority':
                field = ogr.FieldDefn(self._names[b], OGR_TYPES[type(dt(0).item())])
            else:
                field = ogr.FieldDefn(self._names[b], ogr.OFTInteger)
            lyr.CreateField(field)
            # loop points
            for p, point in enumerate(points):
                # fit sampling window
                xOff = int((point[0] - ulx) / resolution) - self._radius
                yOff = int((uly - point[1]) / resolution) - self._radius
                if xOff < 0:
                    xWin = self._radius * 2 - abs(xOff)
                    xOff = 0
                if xOff + (self._radius * 2) > cols:
                    xWin = cols - xOff
                else:
                    xWin = self._radius * 2
                if yOff < 0:
                    yWin = self._radius * 2 - abs(yOff)
                    yOff = 0
                if yOff + (self._radius * 2) > rows:
                    yWin = rows - yOff
                else:
                    yWin = self._radius * 2
                if self._radius == 0:
                    xWin, yWin = (1, 1)
                # read data
                window = band.ReadAsArray(xOff, yOff, xWin, yWin)
                if len(window) > 1:
                    window = window[window != no_data]
                    window = window[window != dt(self._dismiss)]
                else:
                    if window.flatten()[0] == self._dismiss or window.flatten()[0] == no_data:
                        window = np.array([])
                # calculate statistic
                data = self._calculateStats(window, self._mode, no_data)
                # set attribute
                feat = lyr.GetFeature(p)
                feat.SetField(self._names[b], data)
                lyr.SetFeature(feat)
                feat.Destroy()
            band = None
        lyr = None
        ds_points.Destroy()
        ds_img = None
        if self._temp:
            os.remove(self._temp)
        print '\nDuration (hh:mm:ss): \t %s' % (datetime.timedelta(seconds=time.time() - start))
        return True

    # ----------------------------------------------------------------------- #
    # ----------------------------------------------------------------------- #
    # HELPER FUNCTIONS
    def _runCmd(self, command):
        p = sub.Popen(command, stdout=sub.PIPE, stderr=sub.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print command
            print stdout
            print stderr
            sys.exit(1)
        return True

    def _matchProjection(self, shape, raster, match='raster'):
        # get raster information
        ds = gdal.Open(raster)
        wkt = ds.GetProjection()
        srs_raster = osr.SpatialReference(wkt=wkt)
        srs_raster.AutoIdentifyEPSG()
        epsg_raster = int(srs_raster.GetAttrValue('AUTHORITY', 1))
        ds = None
        # get shape projection
        ds = ogr.Open(shape)
        srs_shape = ds.GetLayer().GetSpatialRef()
        srs_shape.AutoIdentifyEPSG()
        epsg_shape = int(srs_shape.GetAttrValue('AUTHORITY', 1))
        ds.Destroy()
        if epsg_raster != epsg_shape:
            if match == 'raster':
                print 'Reprojecting shape to EPSG:{0}'.format(epsg_raster)
                proj_shape = os.path.splitext(shape)[0] + '_projected.shp'
                warnings.warn('Need to re-project points! New output dataset will be {ds}'.format(ds=proj_shape))
                cmd = 'ogr2ogr -overwrite -f "ESRI Shapefile" -t_srs EPSG:{0} {1} {2}'.format(epsg_raster, proj_shape,
                                                                                              shape)
                self._runCmd(cmd)
                shape = proj_shape
                self._temp = None
            else:
                print 'Reprojecting raster to EPSG:{0}'.format(epsg_shape)
                temp_raster = os.path.splitext(raster)[0] + '_projected.tif'
                cmd = 'gdalwarp -of GTiff -overwrite -te_srs EPSG:{0} {1} {2}'.format(epsg_shape, raster, temp_raster)
                self._runCmd(cmd)
                raster = temp_raster
                self._temp = temp_raster
        else:
            print 'Points and raster have the same projection! No reprojection necessary!'
            self._temp = None
        return shape, raster

    def _calculateStats(self, array, mode, noData=None):
        if array.size == 0:
            data = noData
        else:
            if mode == 'median':
                data = np.median(np.ma.masked_invalid(array))
            elif mode == 'mean':
                data = np.nanmean(np.ma.masked_invalid(array))
            elif mode == 'min':
                data = np.nanmin(np.ma.masked_invalid(array))
            elif mode == 'max':
                data = np.nanmax(np.ma.masked_invalid(array))
            elif mode == 'majority':
                if not array.dtype == 'int':
                    warnings.warn('Mode "majority" only works with integer values! Converting accordingly!')
                data = int(np.bincount(array.astype(int).flatten()).argmax())
        return data

# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# run
if __name__ == '__main__':
    app = pointSampling(sys.argv)
    app.run()
