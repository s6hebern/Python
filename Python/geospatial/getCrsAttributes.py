import string

def getEPSG(spatialRef):
    """
    Extract EPSG code from osr.SpatialReference object.

    :param object spatialRef: osr.SpatialReference object
    :return: EPSG code (integer)
    """

    spatialRef.AutoIdentifyEPSG()
    epsg = int(spatialRef.GetAttrValue('AUTHORITY', 1))
    return epsg

def getCrsName(spatialRef):
    """
    Extract spatial reference system name from osr.SpatialReference object

    :param object spatialRef: osr.SpatialReference object
    :return: Name of spatial reference system (string)
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
    :return: Spatial reference unit (string)
    """

    if spatialRef.GetAttrValue('UNIT').lower() == 'degree':
        unit = 'Degrees'
    elif spatialRef.GetAttrValue('UNIT').lower() == 'metre':
        unit = 'Meters'
    else:
        unit = spatialRef.GetAttrValue('UNIT')
        raise UserWarning('Your CRS is neither in degrees nor in meters. Returning standard value!')
    return str(unit)
