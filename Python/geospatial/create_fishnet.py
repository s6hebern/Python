import os
import sys
import time
import datetime
import math
from osgeo import gdal, ogr, osr
from optparse import OptionParser, OptionGroup

gdal.UseExceptions()


class CreateFishnet(object):
    def __init__(self, argv):
        print('Running CreateFishnet...\n')
        self._format = None
        self._cols = None
        self._rows = None
        self._extent = None
        self._hSpace = None
        self._vSpace = None
        self._adjust = False
        self._overwrite = False
        self._spatialRef = None
        self._grid = None

    def setup_option_parser(self):
        parser = OptionParser('''
Description:
    Create a vector grid of equally sized polygons.
''', conflict_handler='resolve')
        group = OptionGroup(parser, 'Mandatory Options', 'Must be defined')
        group.add_option('-e', '--extent', dest='extent',
                         help='Extent of the grid. Can either be taken from a gdal or ogr '
                              'datasource (raster or vector file) or parsed as a comma-separated '
                              'list of coordinates and their EPSG-code (no space) in order (x_min, '
                              'x_max, y_min, y_max, EPSG)')
        group.add_option('-g', '--grid', dest='grid',
                         help='Output grid with respective file extension')
        parser.add_option_group(group)

        group = OptionGroup(parser, 'Additional Mandatory Options',
                            'Either columns/rows or width/height must be defined')
        group.add_option('-c', '--columns', dest='cols', help='Number of grid columns')
        group.add_option('-r', '--rows', dest='rows', help='Number of grid rows')
        group.add_option('-w', '--width', dest='width',
                         help='Grid cell width (in input projection units)')
        group.add_option('-h', '--height', dest='height',
                         help='Grid cell height (in input projection units)')
        parser.add_option_group(group)

        group = OptionGroup(parser, 'Additional Options', 'Can be defined')
        group.add_option('-f', '--format', dest='format', default='ESRI Shapefile',
                         help='File format for output. Default is "ESRI Shapefile". See '
                               'http://www.gdal.org/ogr_formats.html for valid codes')
        group.add_option('-a', '--adjust', dest='adjust', default='expand',
                         help='Adjustment of grid extent if cell width and height do not match '
                              'exactly with given extent. Either "expand" (default; extent will '
                              'become greater) or "shrink" (extent will become smaller')
        group.add_option('-o', '--overwrite', dest='overwrite', action='store_true', default=False,
                         help='Overwrite output if it already exists')
        parser.add_option_group(group)
        return parser

    def check_options(self):
        parser = self.setup_option_parser()
        (options, args) = parser.parse_args()
        self._format = options.format
        self._overwrite = options.overwrite
        self._adjust = options.adjust
        if not options.extent:
            parser.print_help()
            raise IOError('No input file given!')
        else:
            self._extent = options.extent
            if os.path.isfile(self._extent):                # extent from file
                self._extent = self._get_extent(self._extent)
                if not options.cols or not options.rows:    # grid spacing must be defined
                    if not options.width or not options.height:
                        parser.print_help()
                        raise IOError('Neither grid spacing nor cols and rows are defined!')
                    else:
                        self._hSpace = float(options.width)
                        self._vSpace = float(options.height)
                        # calculate cols and rows
                        self._cols, self._rows = self._get_cols_rows(self._extent, self._hSpace, self._vSpace)
                else:
                    self._cols = int(options.cols)
                    self._rows = int(options.rows)
                    # calculate grid spacing
                    self._hSpace, self._vSpace = self._get_grid_spacing(self._extent, self._cols, self._rows)
            else:                                           # extent given by user
                if not options.width or not options.height:
                    parser.print_help()
                    raise IOError('No grid spacing given!')
                else:
                    self._hSpace = float(options.width)
                    self._vSpace = float(options.height)
                    epsg = int(self._extent.split(',')[-1])
                    self._spatialRef = osr.SpatialReference()
                    self._spatialRef.ImportFromEPSG(epsg)
                    self._extent = self._extent.split(',')[:4]
                self._cols = int(options.cols)
                self._rows = int(options.rows)
            print('Using extent {0}'.format(self._extent))
            print('Grid spacing (h/v): \t{0}\t{1}'.format(self._hSpace, self._vSpace))
        if not options.grid:
            parser.print_help()
            raise IOError('No output file given!')
        else:
            self._grid = options.grid
        return True

    def run(self):
        self.check_options()
        ds, lyr = self._create_ds(self._grid, self._spatialRef)
        x_min = float(self._extent[0])
        y_max = float(self._extent[3])
        # first polygon
        poly_xmin = x_min
        poly_xmax = x_min + self._hSpace
        poly_ymin = y_max
        poly_ymax = y_max - self._vSpace
        # loop polygon creation
        for colcount in range(self._cols):
            ring_ymax = poly_ymax
            ring_ymin = poly_ymin
            for rowcount in range(self._rows):
                ring = ogr.Geometry(ogr.wkbLinearRing)
                ring.AddPoint(poly_xmin, ring_ymax)
                ring.AddPoint(poly_xmax, ring_ymax)
                ring.AddPoint(poly_xmax, ring_ymin)
                ring.AddPoint(poly_xmin, ring_ymin)
                ring.AddPoint(poly_xmin, ring_ymax)
                poly = ogr.Geometry(ogr.wkbPolygon)
                poly.AddGeometry(ring)
                # add polygon to layer
                featureDefn = lyr.GetLayerDefn()
                feature = ogr.Feature(featureDefn)
                feature.SetGeometry(poly)
                lyr.CreateFeature(feature)
                feature.Destroy()
                # new extent for polygon in next row
                ring_ymax = ring_ymax - self._vSpace
                ring_ymin = ring_ymin - self._vSpace
            # new extent for polygon in next column
            poly_xmin = poly_xmin + self._hSpace
            poly_xmax = poly_xmax + self._hSpace
        ds.Destroy()

# --------------------------------------------------------------------------- #
# HELPER FUNCTIONS
    def _get_extent(self, dataset):
        if not os.path.isfile(dataset):
            raise TypeError('Given dataset is not a file!')
        try:
            ds = gdal.Open(dataset, gdal.GA_ReadOnly)   # raster
            ds_type = 'raster'
        except:
            try:
                ds = ogr.Open(dataset, 0)               # vector
                ds_type = 'vector'
            except:
                raise TypeError('Given dataset is not compatible with GDAL or OGR!')
        # open and get extent
        if ds_type == 'raster':
            geotrans = ds.GetGeoTransform()
            x_min = geotrans[0]
            x_max = x_min + (geotrans[1] * ds.RasterXSize)
            y_max = geotrans[3]
            y_min = y_max - (abs(geotrans[5]) * ds.RasterYSize)
            self._spatialRef = osr.SpatialReference()
            self._spatialRef.ImportFromWkt(ds.GetProjection())
            ds = None
        else:
            lyr = ds.GetLayer(os.path.split(os.path.splitext(dataset)[0])[1])
            x_min, x_max, y_min, y_max = lyr.GetExtent()
            self._spatialRef = (ds.GetLayer().GetSpatialRef())
            ds.Destroy()
        extent = [x_min, x_max, y_min, y_max]
        return extent

    def _create_ds(self, dataset, srs):
        drv = ogr.GetDriverByName(self._format)
        if os.path.exists(dataset) and self._overwrite is True:
            self._delete_ds(dataset)
        elif os.path.exists(dataset) and self._overwrite is False:
            print('ERROR: Output grid {0} already exists and shall not be overwritten!'.format(dataset))
            sys.exit(1)
        ds = drv.CreateDataSource(dataset)
        lyr_name = os.path.splitext(os.path.basename(dataset))[0]
        lyr = ds.CreateLayer(lyr_name, srs, ogr.wkbPolygon)
        return ds, lyr

    def _delete_ds(self, dataset):
        drv = ogr.GetDriverByName(self._format)
        drv.DeleteDataSource(dataset)
        drv = None
        return True

    def _get_grid_spacing(self, extent, cols, rows):
        gridHspace = (extent[1] - extent[0]) / cols
        gridVspace = (extent[3] - extent[2]) / rows
        return gridHspace, gridVspace

    def _get_cols_rows(self, extent, hspace, vspace):
        if self._adjust == 'expand':
            cols = math.ceil((extent[1] - extent[0]) / vspace)
            rows = math.ceil((extent[3] - extent[2]) / hspace)
        else:
            cols = math.floor((extent[1] - extent[0]) / vspace)
            rows = math.floor((extent[3] - extent[2]) / hspace)
        return int(cols), int(rows)


if __name__ == '__main__':
    start = time.time()
    app = CreateFishnet(sys.argv)
    app.setup_option_parser()
    app.check_options()
    app.run()
    print('Duration (hh:mm:ss): \t %s' % (datetime.timedelta(seconds=time.time() - start)))
