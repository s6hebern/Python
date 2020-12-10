import sys
import warnings
import math
import fnmatch
import utm
import geopy.distance as distance
from osgeo import osr

osr.UseExceptions()


def check_installed_epsg(epsg, silent=False):
    # type: (int, bool) -> bool
    """
    Check if given EPSG code is installed and supported

    :param epsg: EPSG code
    :param silent: If True, a message is printed out
    :return: True if installed, False if not
    """
    if 'win' in sys.platform.lower():
        epsg_db = r'c:\Program Files\GDAL\projlib\epsg'
    else:
        epsg_db = r'/usr/share/proj/epsg'
    with open(epsg_db, 'r') as f:
        lines = f.readlines()
    stmt = 'Given EPSG code {e} '.format(e=epsg)
    for l in lines:
        if ''.join(['<', str(epsg), '>']) in l:
            try:
                sr = osr.SpatialReference()
                sr.ImportFromEPSG(epsg)
                stmt += 'is valid!'
                if not silent:
                    print(stmt)
                return True
            except:
                stmt += 'was found, but could not be imported!'
                if not silent:
                    print(stmt)
                return False
    stmt += 'was not found!'
    if not silent:
        print(stmt)
    return False


def get_epsg(spatial_ref):
    # type: (osr.SpatialReference) -> int
    """
    Extract EPSG code from osr.SpatialReference object.

    :param spatial_ref: osr.SpatialReference object
    :return: EPSG code
    """
    try:
        spatial_ref.AutoIdentifyEPSG()
        return int(spatial_ref.GetAttrValue('AUTHORITY', 1))
    except RuntimeError:
        print('Could not auto-identify EPSG code! Trying to look it up in the database...')
        proj_4 = spatial_ref.ExportToProj4()
        pattern = '*' + '*'.join(proj_4.split(' '))
        if 'win' in sys.platform.lower():
            epsg_db = r'c:\Program Files\GDAL\projlib\epsg'
        else:
            epsg_db = r'/usr/share/proj/epsg'
        with open(epsg_db, 'r') as f:
            lines = f.readlines()
        results = []
        for l in lines:
            if fnmatch.fnmatch(l, pattern):
                epsg = int(l.split('>')[0].split('<')[-1])
                results.append(epsg)
        if len(results) > 1:
            warnings.warn('Found more than one match! Choosing the one with the "largest" EPSG code!')
            return sorted(results)[-1]
        return False


def get_crs_name(spatial_ref):
    # type: (osr.SpatialReference) -> str
    """
    Extract spatial reference system name from osr.SpatialReference object

    :param object spatial_ref: osr.SpatialReference object
    :return: Name of spatial reference system
    """
    if spatial_ref.IsGeographic():
        srs_name = str(spatial_ref.GetAttrValue('GEOGCS'))
    else:
        srs_name = str(spatial_ref.GetAttrValue('PROJCS'))
    if '_' in srs_name:
        srs_name = str(' '.join(srs_name.split('_')))
    return srs_name


def get_crs_unit(spatial_ref):
    # type: (osr.SpatialReference) -> str
    """
    Extract measuring unit from osr.SpatialReference object

    :param spatial_ref: osr.SpatialReference object
    :return: Spatial reference unit
    """
    if spatial_ref.GetAttrValue('UNIT').lower() == 'degree':
        unit = 'Degrees'
    elif spatial_ref.GetAttrValue('UNIT').lower() == 'metre':
        unit = 'Meters'
    else:
        unit = spatial_ref.GetAttrValue('UNIT')
        raise UserWarning('Your CRS is neither in degrees nor in meters. Returning standard value!')
    return str(unit)


def get_utm_zone(x, y, epsg_in=4326):
    # type: (float, float, int) -> (int, str)
    """
    Get UTM zone from a given coordinate.

    :param x: x-coordinate
    :param y: y-coordinate
    :param epsg_in: EPSG code of input coordinates
    :return: Tuple of UTM zone number as integer and Hemisphere as string
    """
    if epsg_in != 4326:
        x, y = project_coords_epsg(x, y, epsg_in, 4326)
    zone_num = utm.latlon_to_zone_number(y, x)
    zone_letter = utm.latitude_to_zone_letter(y)
    zone_letter = 'N' if zone_letter > 'M' else 'S'
    return zone_num, zone_letter


def project_coords_wkt(x, y, wkt_in, wkt_out):
    # type: (float, float, str, str) -> (float, float)
    """
    Transform point coordinates based on WKT-representations of spatial reference systems (SRS)

    :param x: x-coordinate
    :param y: y-coordinate
    :param wkt_in: WKT-representation of input SRS
    :param wkt_out: WKT-representation of output SRS
    :return: Transformed coordinates (x, y)
    """
    src_sr = osr.SpatialReference()
    trgt_sr = osr.SpatialReference()
    src_sr.ImportFromWkt(wkt_in)
    trgt_sr.ImportFromWkt(wkt_out)
    transformer = osr.CoordinateTransformation(src_sr, trgt_sr)
    new_point = transformer.TransformPoint(x, y)
    new_x = new_point[0]
    new_y = new_point[1]
    return new_x, new_y


def project_coords_epsg(x, y, epsg_in, epsg_out):
    # type: (float, float, int, int) -> (float, float)
    """
    Transform point coordinates based on EPSG-code of spatial reference systems (SRS)

    :param int/float x: x-coordinate
    :param int/float y: y-coordinate
    :param epsg_in: EPSG-code of input SRS
    :param epsg_out: EPSG-code of output SRS
    :return: transformed coordinates (x, y)
    :rtype: tuple
    """
    src_sr = osr.SpatialReference()
    trgt_sr = osr.SpatialReference()
    src_sr.ImportFromEPSG(epsg_in)
    trgt_sr.ImportFromEPSG(epsg_out)
    transformer = osr.CoordinateTransformation(src_sr, trgt_sr)
    new_point = transformer.TransformPoint(x, y)
    new_x = new_point[0]
    new_y = new_point[1]
    return new_x, new_y


def geo_to_pixel_coords(x, y, geotrans, cols, rows):
    # type: (float, float, tuple, int, int) -> (int, int)
    """
    Convert geo-coordinates to grid-coordinates

    :param x: x-coordinate
    :param y: y-coordinate
    :param cols: number of columns of input image (x-size)
    :param rows: number of rows of input image (y-size)
    :param geotrans: GeoTransformObject from gdalDataSource or tuple with (xMin, cellWidth,
            xRotation, yMax, yRotation, cellHeight). cellHeight has to be negative!
    :return: Column and row at given position (col, row)
    """
    ulx = geotrans[0]
    uly = geotrans[3]
    lrx = geotrans[0] + cols * geotrans[1]
    lry = geotrans[3] + rows * geotrans[5]
    if x < ulx or x > lrx or y < lry or y > uly:
        raise ValueError('Coordinate is outside the image!')
    # do the math
    x_pix = int(math.floor((x - ulx) / geotrans[1]))
    y_pix = int(math.floor((uly - y) / -geotrans[5]))
    return x_pix, y_pix


def pixel_to_geo_coords(col, row, geotrans, loc='center'):
    # type: (int, int, tuple, str) -> (float, float)
    """
    Convert grid-coordinates to geo-coordinates

    :param col: column number (counting starts at 0)
    :param row: row number (counting starts at 0)
    :param geotrans: GeoTransformObject from gdalDataSource or tuple with (xMin, cellWidth,
            xRotation, yMax, yRotation, cellHeight). cellHeight has to be nagtive!
    :param loc: location within the pixel. One of "center", "ul", "ur", "ll", "lr"
    :return: Coordinates at given grid cell (x, y)
    """
    ulx = geotrans[0]
    xres = geotrans[1]
    xrot = geotrans[2]
    uly = geotrans[3]
    yrot = geotrans[4]
    yres = geotrans[5]
    # do the math
    if loc == 'center':
        xgeo = ulx + col * xres + xres / 2. + row * xrot
        ygeo = uly + row * yres + yres / 2. + col * yrot
    elif loc == 'ul':
        xgeo = ulx + col * xres + row * xrot
        ygeo = uly + row * yres + col * yrot
    elif loc == 'll':
        xgeo = ulx + col * xres + row * xrot
        ygeo = uly + row * yres + yres + col * yrot
    elif loc == 'ur':
        xgeo = ulx + col * xres + xres + row * xrot
        ygeo = uly + row * yres + col * yrot
    elif loc == 'lr':
        xgeo = ulx + col * xres + xres + row * xrot
        ygeo = uly + row * yres + yres + col * yrot
    else:
        raise ValueError('loc only takes one of "center", "ul", "ur", "ll", "lr"!')
    return xgeo, ygeo


def get_point_distance(p1, p2, unit='m'):
    # type: (tuple, tuple, str) -> float
    """
    Calculate the distance between two points

    :param p1: x-y tuple
    :param p2: x-y tuple
    :param unit: Output measurement unit. One of 'm', 'km', 'miles', 'nautical miles', 'feet'
    :return: Distance in desired unit
    """
    dist = distance.distance(p1, p2)
    if unit.lower() == 'm':
        dist = dist.m
    elif unit.lower() == 'km':
        dist = dist.km
    elif unit.lower() == 'miles':
        dist = dist.mi
    elif unit.lower() == 'nautical miles':
        dist = dist.nm
    elif unit.lower() == 'feet':
        dist = dist.ft
    else:
        raise ValueError('Wrong unit!')
    return dist


def dec_deg_to_dms(dec_deg):
    # type: (float) -> (int, int, float)
    """
    Convert decimal degrees to degrees minutes seconds

    :param dec_deg: Coordinate represented as decimal degree (like 49.854276). Use negative
            values for South/West.
    :return: Coordinate represented as degrees minutes seconds
    """
    mnt, sec = divmod(dec_deg * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return deg, mnt, sec


def dms_to_dec_deg(dms):
    # type: (tuple) -> float
    """
    Convert degrees minutes seconds to decimal degrees

    :param dms: Coordinate represented as tuple of length 3 (like (49.0, 51.0, 15.3936). Use
            negative values of degrees, minutes and seconds for South/West (all three must be
            negative then).
    :return: Coordinate represented as decimal degrees
    """
    if len(dms) != 3:
        raise ValueError('Coordinate tuple needs exactly 3 elements (degrees, minutes, seconds)!')
    deg, mnt, sec = dms
    dd = float(deg) + float(mnt)/60. + float(sec) / (60. * 60.)
    return dd


if __name__ == '__main__':
    print(dms_to_dec_deg((27, 10, 23.73)), dms_to_dec_deg((-90, -21, -56.28)))
    print(dms_to_dec_deg((24, 24, 58.36)), dms_to_dec_deg((-12, -27, -59.322)))

