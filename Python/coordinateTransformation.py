import math
from osgeo import osr


def projectCoordsWkt(x, y, wkt_in, wkt_out):
    """
    Transform point coordinates based on WKT-representations of spatial reference systems (SRS)

    :param int/float x: x-coordinate
    :param int/float y: y-coordinate
    :param str wkt_in: WKT-representation of input SRS
    :param str wkt_out: WKT-representation of output SRS
    :return: transformed coordinates (x, y)
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
    :return:
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
