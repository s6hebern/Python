import math
import string
import utm
from osgeo import osr


def getEPSG(spatialRef):
    """
    Extract EPSG code from osr.SpatialReference object.

    :param object spatialRef: osr.SpatialReference object
    :return: EPSG code
    :rtype: int
    """

    spatialRef.AutoIdentifyEPSG()
    epsg = int(spatialRef.GetAttrValue('AUTHORITY', 1))
    return epsg


def getCrsName(spatialRef):
    """
    Extract spatial reference system name from osr.SpatialReference object

    :param object spatialRef: osr.SpatialReference object
    :return: Name of spatial reference system
    :rtype: str
    """

    if spatialRef.IsGeographic():
        srs_name = str(spatialRef.GetAttrValue('GEOGCS'))
    else:
        srs_name = str(spatialRef.GetAttrValue('PROJCS'))
    if '_' in srs_name:
        srs_name = str(string.join(srs_name.split('_')))
    return srs_name


def getCrsUnit(spatialRef):
    """
    Extract measuring unit from osr.SpatialReference object

    :param object spatialRef: osr.SpatialReference object
    :return: Spatial reference unit
    :rtype: str
    """

    if spatialRef.GetAttrValue('UNIT').lower() == 'degree':
        unit = 'Degrees'
    elif spatialRef.GetAttrValue('UNIT').lower() == 'metre':
        unit = 'Meters'
    else:
        unit = spatialRef.GetAttrValue('UNIT')
        raise UserWarning('Your CRS is neither in degrees nor in meters. Returning standard value!')
    return str(unit)


def getUtmZone(x, y, epsg_in=4326):
    """
    Get UTM zone from a given coordinate.

    :param numeric x: x-coordinate
    :param numeric y: y-coordinate
    :param int epsg_in: EPSG code of input coordinates
    :return: Tuple of UTM zone number as integer and Hemisphere as string
    :rtype: tuple
    """

    if epsg_in != 4326:
        x, y = projectCoordsEPSG(x, y, epsg_in, 4326)
    zone_num = utm.latlon_to_zone_number(y, x)
    zone_letter = utm.latitude_to_zone_letter(y)
    zone_letter = 'N' if zone_letter > 'M' else 'S'
    return zone_num, zone_letter


def projectCoordsWkt(x, y, wkt_in, wkt_out):
    """
    Transform point coordinates based on WKT-representations of spatial reference systems (SRS)

    :param int/float x: x-coordinate
    :param int/float y: y-coordinate
    :param str wkt_in: WKT-representation of input SRS
    :param str wkt_out: WKT-representation of output SRS
    :return: transformed coordinates (x, y)
    :rtype: tuple
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


def projectCoordsEPSG(x, y, epsg_in, epsg_out):
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


def geoToPixelCoords(x, y, geotrans):
    """
    Return grid-coordinates from geo-coordinates

    :param int/float x: x-coordinate
    :param int/float y: y-coordinate
    :param tuple geotrans: GeoTransformObject from gdalDataSource or tuple with (xMin, cellWidth, xRotation, yMax,
                            yRotation, cellHeight). cellHeight has to be nagtive!
    :return: Column and row at given position (col, row)
    :rtype: tuple
    """

    ulx = geotrans[0]
    uly = geotrans[3]
    # do the math
    col = int(math.floor((x - ulx) / geotrans[1]))
    row = int(math.floor((uly - y) / -geotrans[5]))
    return col, row


def pixelToGeoCoords(col, row, geotrans, loc='center'):
    """
    Return geo-coordinates from grid-coordinates

    :param number col: column number (counting starts at 0)
    :param number row: row number (counting starts at 0)
    :param tuple geotrans: GeoTransformObject from gdalDataSource or tuple with (xMin, cellWidth, xRotation, yMax,
                            yRotation, cellHeight). cellHeight has to be nagtive!
    :param str loc: location within the pixel. One of "center", "ul", "ur", "ll", "lr"
    :return: Coordinates at given grid cell (x, y)
    :rtype: tuple
    """

    ulx = geotrans[0]
    xres = geotrans[1]
    xrot = geotrans[2]
    uly = geotrans[3]
    yrot = geotrans[4]
    yres = geotrans[5]
    # do the math
    if loc == 'center':
        xgeo = ulx + col * xres + xres / 2 + row * xrot
        ygeo = uly + row * yres + yres / 2 + col * yrot
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


def DD2DMS(dd):
    """
    Convert decimal degrees to degrees minutes seconds

    :param float dd: Coordinate represented as decimal degree (like 49.854276). Use negative values for South/West.
    :return: Coordinate represented as degrees minutes seconds
    :rtype: tuple
    """

    mnt, sec = divmod(dd * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return deg, mnt, sec


def DMS2DD(dms):
    """
    Convert degrees minutes seconds to decimal degrees

    :param tuple dms: Coordinate represented as tuple of length 3 (like (49.0, 51.0, 15.3936). Use negative values of
        degrees for South/West.
    :return: Coordinate represented as decimal degrees
    :rtype: float
    """

    if len(dms) != 3:
        raise ValueError('Coordinate tuple has have exactly 3 elements (degrees, minutes, seconds)!')
    deg, mnt, sec = dms
    dd = float(deg) + mnt/60. + sec/(60*60)
    return dd
