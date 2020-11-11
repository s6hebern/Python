import os
import warnings
import string
from tqdm import tqdm
from osgeo import ogr, osr
from collections import Counter


OGR_FIELD_TYPES = [
    ogr.OFTBinary,
    ogr.OFTDate,
    ogr.OFTDateTime,
    ogr.OFTInteger,
    ogr.OFTIntegerList,
    ogr.OFTReal,
    ogr.OFTRealList,
    ogr.OFTString,
    ogr.OFTStringList,
    ogr.OFTTime,
    ogr.OFTWideString,
    ogr.OFTWideStringList
]


def create_ds(ds_name, ds_format, geom_type, srs, overwrite=False):
    # type: (str, str, ogr.Geometry, osr.SpatialReference, bool) -> (ogr.DataSource, ogr.Layer)
    """
    Create an OGR Dataset and Layer. Remember to call ds.Destroy() after you finished editing it!

    :param ds_name: Output filename.
    :param ds_format: File format.
    :param geom_type: OGR Geometry Type
    :param srs: OSR Spatial Reference Object
    :param overwrite: Overwrite output file, if it already exists
    :return: (ogr.Dataset, ogr.Layer)
    :rtype: tuple
    """
    drv = ogr.GetDriverByName(ds_format)
    if os.path.exists(ds_name) and overwrite is True:
        delete_ds(ds_name)
    elif os.path.exists(ds_name) and overwrite is False:
        raise StandardError('{f} already exists and shall not be overwritten!'.format(f=ds_name))
    ds = drv.CreateDataSource(ds_name)
    lyr_name = os.path.splitext(os.path.basename(ds_name))[0]
    lyr = ds.CreateLayer(lyr_name, srs, geom_type)
    return ds, lyr


def delete_ds(ds_name):
    # type: (str) -> None
    """
    Delete an OGR Dataset

    :param ds_name: File to delete.
    :return: --
    """
    ds = ogr.Open(ds_name)
    drv = ds.GetDriver()
    ds.Destroy()
    drv.DeleteDataSource(ds_name)
    return


def copy_ds(src, dst, overwrite=False):
    # type: (str, str, bool) -> None
    """
    Copy a vector file

    :param src: Source filename
    :param dst: Destination filename
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    if os.path.exists(dst) and overwrite is True:
        delete_ds(dst)
    elif os.path.exists(dst) and overwrite is False:
        raise StandardError('{f} already exists and shall not be overwritten!'.format(f=dst))
    ds = ogr.Open(src)
    drv = ds.GetDriver()
    out_ds = drv.CopyDataSource(ds, dst)
    out_ds.Destroy()
    ds.Destroy()
    return


def create_field(ds_name, field_name, field_type, field_width, field_precision=None, initial_value=None):
    # type: (str, str, ogr.FieldDefn, int, int, any) -> None
    """
    Create a new attribute field

    :param ds_name: Input file (will be updated)
    :param field_name: New field name
    :param field_type: OGR filed type. One of: ogr.OFTBinary, ogr.OFTDate, ogr.OFTDateTime, ogr.OFTInteger, ogr.OFTIntegerList, ogr.OFTReal, ogr.OFTRealList, ogr.OFTString, ogr.OFTStringList, ogr.OFTTime, ogr.OFTWideString, ogr.OFTWideStringList
    :param field_width: Field width. For safety, use one more than the lenght of your maximum value
    :param field_precision: Field precision (only needed for floating point field)
    :param initial_value: Default value for all features. Data type needs to match the chosen field_type
    :return: --
    """
    if not os.path.exists(ds_name):
        raise IOError('Input file {f} does not exist!'.format(f=ds_name))
    if len(field_name) > 10:
        warnings.warn('Field name {n} contains more than 10 characters and will therefore be truncated to 10 for '
                      'safety!'.format(n=field_name))
    if field_type not in OGR_FIELD_TYPES:
        raise ValueError('Given field type not supported by OGR! Use one of the following: {types}'.format(
            types=', '.join([t for t in OGR_FIELD_TYPES])))
    print('Creating field {f} as new attribute for {ds}...'.format(f=field_name, ds=ds_name))
    ds = ogr.Open(ds_name, 1)
    lyr = ds.GetLayer()
    field_defn = lyr.GetLayerDefn()
    fieldnames = [field_defn.GetFieldDefn(f).name.lower() for f in range(field_defn.GetFieldCount())]
    if field_name.lower() in fieldnames:
        ds.Destroy()
        raise KeyError('Chosen field name "{n}" already exists!'.format(n=field_name))
    field_defn = ogr.FieldDefn(field_name, field_type)
    field_defn.SetWidth(int(field_width))
    if field_precision:
        field_defn.SetPrecision(int(field_precision))
    lyr.CreateField(field_defn)
    if initial_value != None:
        for feature in tqdm(lyr, desc='Setting initial value'):
            feature.SetField(field_name, initial_value)
            lyr.SetFeature(feature)
    repack(ds, lyr)
    ds.Destroy()
    print('Done!')
    return


def repack(ds, lyr):
    # type: (ogr.DataSource, ogr.Layer) -> None
    """
    Flush pending changes on the layer and repack the file to make everything permanent

    :param ds: Input OGR Dataset
    :param lyr: OGR LayerShadow from ds
    :return: --
    """
    # lyr.SyncToDisc()
    ds.ExecuteSQL('REPACK {n}'.format(n=lyr.GetName()))
    return


def close_rings(ds_name):
    # type: (str) -> None
    """
    Close rings within a polygon vector file.

    :param ds_name:
    :return: --
    """
    ds = ogr.Open(ds_name, 1)
    lyr = ds.GetLayer()
    copies = []
    for feat in lyr:
        if feat.geometry():
            feat.geometry().CloseRings()
            copies.append(feat)
            lyr.DeleteFeature(feat.GetFID())
    for copy in copies:
        lyr.CreateFeature(copy)
    repack(ds, lyr)
    ds.Destroy()
    return


def getExtent(input):
    """
    Get maximum the extent of an OGR Dataset

    :param str input: Input filename
    :return: Extent as a tuple of (xmin, ymin, xmax, ymax)
    :rtype tuple
    """

    ds = ogr.Open(input)
    lyr = ds.GetLayer()
    ulx, lrx, uly, lry = lyr.GetExtent()
    ds.Destroy()
    return ulx, uly, lrx, lry


def create_points_from_coords(outfile, coords, epsg=4326, outformat='ESRI Shapefile', overwrite=False):
    # type: (str, (float, float), int, str, bool) -> None
    """
    Create a point vector file from a list of xy-coordinates

    :param outfile: Output file
    :param coords: Iterable (list or tuple) of tuple(s) with xy-coordinates (as floats)
    :param epsg: EPSG code of given coordinates
    :param outformat: Output format according to OGR driver standard
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    if os.path.exists(outfile):
        if overwrite is True:
            delete_ds(outfile)
        else:
            raise IOError('File {f} already exists and shall not be overwritten!'.format(f=outfile))
    try:
        ogr.GetDriverByName(outformat)
    except:
        raise AttributeError('Wrong output format {of}!'.format(of=outformat))
    srs = osr.SpatialReference()
    try:
        srs.ImportFromEPSG(epsg)
    except:
        raise AttributeError('Invalid EPSG code {e}!'.format(e=epsg))
    ds, lyr = create_ds(outfile, outformat, ogr.wkbPoint, srs, overwrite)
    for xy in coords:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(xy[0], xy[1])
        defn = lyr.GetLayerDefn()
        feat = ogr.Feature(defn)
        geom = ogr.CreateGeometryFromWkb(point.ExportToWkb())
        feat.SetGeometry(geom)
        lyr.CreateFeature(feat)
        feat = None
        geom = None
    lyr = ds = None
    return


def create_polygon_from_bbox(outfile, ulx, uly, lrx, lry, epsg=4326, outformat='ESRI Shapefile', overwrite=False):
    # type: (str, float, float, float, float, int, str, bool) -> None
    """
    Create a rectangular polygon from its corner coordinates

    :param outfile: Output file
    :param ulx: Latitude / x of upper left corner
    :param uly: Longitude / y of upper left corner
    :param lrx: Latitude / x of lower right corner
    :param lry: Longitude / y of lower right corner
    :param epsg: EPSG code of given coordinates
    :param outformat: Output format according to OGR driver standard
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    if os.path.exists(outfile):
        if overwrite is True:
            delete_ds(outfile)
        else:
            raise IOError('File {f} already exists and shall not be overwritten!'.format(f=outfile))
    try:
        ogr.GetDriverByName(outformat)
    except:
        raise AttributeError('Wrong output format {of}!'.format(of=outformat))
    srs = osr.SpatialReference()
    try:
        srs.ImportFromEPSG(epsg)
    except:
        raise AttributeError('Invalid EPSG code {e}!'.format(e=epsg))
    ds, lyr = create_ds(outfile, outformat, ogr.wkbPolygon, srs, overwrite)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(float(ulx), float(uly))
    ring.AddPoint(float(lrx), float(uly))
    ring.AddPoint(float(lrx), float(lry))
    ring.AddPoint(float(ulx), float(lry))
    ring.CloseRings()
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    defn = lyr.GetLayerDefn()
    feat = ogr.Feature(defn)
    geom = ogr.CreateGeometryFromWkb(poly.ExportToWkb())
    feat.SetGeometry(geom)
    lyr.CreateFeature(feat)
    feat = geom = lyr = ds = None
    return


def create_polygon_from_coords(outfile, coords, epsg=4326, outformat='ESRI Shapefile', overwrite=False):
    # type: (str, (tuple, tuple, ...), int, str, bool) -> None
    """
    Create a polygon from a list of coordinate tuples

    :param outfile: Output file
    :param coords: Iterable (list, tuple) of (x, y) tuples holding the coordinates. The Polygon will vertices be
    drawn in the given order.
    :param epsg: EPSG code of given coordinates
    :param outformat: Output format according to OGR driver standard
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    if os.path.exists(outfile):
        if overwrite is True:
            delete_ds(outfile)
        else:
            raise IOError('File {f} already exists and shall not be overwritten!'.format(f=outfile))
    try:
        ogr.GetDriverByName(outformat)
    except:
        raise AttributeError('Wrong output format {of}!'.format(of=outformat))
    srs = osr.SpatialReference()
    try:
        srs.ImportFromEPSG(epsg)
    except:
        raise AttributeError('Invalid EPSG code {e}!'.format(e=epsg))
    ds, lyr = create_ds(outfile, outformat, ogr.wkbPolygon, srs, overwrite)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in coords:
        ring.AddPoint(x, y)
    ring.CloseRings()
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    defn = lyr.GetLayerDefn()
    feat = ogr.Feature(defn)
    geom = ogr.CreateGeometryFromWkb(poly.ExportToWkb())
    feat.SetGeometry(geom)
    lyr.CreateFeature(feat)
    feat = geom = lyr = ds = None
    return


def assign_projection(input, epsg):
    # type: (str, int) -> None
    """
    Create a *.prj file for the given input vector file

    :param input: Path to vector file
    :param epsg: EPSG code of the desired coordinate system
    :return: --
    """
    prj = os.path.splitext(input)[0] + '.prj'
    sr = osr.SpatialReference()
    try:
        sr.ImportFromEPSG(epsg)
    except:
        raise ValueError('Import of EPSG code {e} failed! Are you sure this is a valid EPSG code?'.format(e=epsg))
    wkt = sr.ExportToWkt()
    with open(prj, 'w') as p:
        p.write(wkt)
    return


def reproject(ds_name, epsg, output, overwrite=False):
    # type: (str, int, str, bool) -> None
    """
    (Re)project a vector file

    :param ds_name: Input filename
    :param epsg: EPSG-code of output coordinate system
    :param output: Output filename
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    in_ds = ogr.Open(ds_name)
    in_lyr = in_ds.GetLayer()
    in_srs = in_lyr.GetSpatialRef()
    if not in_srs:
        raise StandardError('{s} has no spatial reference!'.format(s=ds_name))
    out_srs = osr.SpatialReference()
    out_srs.ImportFromEPSG(epsg)
    ds, lyr = create_ds(output, in_ds.GetDriver().GetName(), in_lyr.GetGeomType(), out_srs, overwrite)
    f_defn = lyr.GetLayerDefn()
    transformer = osr.CoordinateTransformation(in_srs, out_srs)
    feature = in_lyr.GetFeature(0)
    for f in range(len(feature.keys())):
        lyr.CreateField(feature.GetFieldDefnRef(f))
    feature.Destroy()
    for feature in in_lyr:
        geom = feature.GetGeometryRef()
        geom.Transform(transformer)
        out_feat = ogr.Feature(f_defn)
        out_feat.SetGeometry(geom)
        # get attribute fields
        for key in feature.keys():
            out_feat.SetField(feature.keys().index(key), feature.GetField(key))
        lyr.CreateFeature(out_feat)
        feature.Destroy()
    ds.Destroy()
    in_ds.Destroy()
    return


def merge(files, output, overwrite=True):
    # type: (list or tuple, str, bool) -> None
    """
    Merge vector files (assuming they share the same coordinate system)

    :param files: List of input files of the same geometry type (e.g. all polygons)
    :param output: Output file
    :param overwrite: Overwrite output, if it already exists
    :return: --
    """
    geom_types = []
    for f in files:
        ds = ogr.Open(f)
        lyr = ds.GetLayer()
        geom_types.append(lyr.GetGeomType())
        ds.Destroy()
    if len(set(geom_types)) != 1:
        raise AttributeError('Input files have different geometry types!')
    # initiate output
    if os.path.exists(output) and overwrite is True:
        delete_ds(output)
    elif os.path.exists(output) and overwrite is False:
        raise ValueError('Output file {out} already exists and shall not be overwritten! Please choose another name or '
                         'set overwrite=True.'.format(out=output))
    ds = ogr.Open(files[0])
    lyr = ds.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    drv = ds.GetDriver()
    ds.Destroy()
    out_ds, out_lyr = create_ds(output, drv.GetName(), geom_types[0], srs)
    featureDefn = out_lyr.GetLayerDefn()
    # merge
    for f in files:
        ds = ogr.Open(f)
        lyr = ds.GetLayer()
        for feature in range(lyr.GetFeatureCount()):
            feat = lyr.GetFeature(feature)
            out_feat = ogr.Feature(featureDefn)
            out_feat.SetGeometry(feat.GetGeometryRef())
            out_lyr.CreateFeature(out_feat)
            out_feat.Destroy()
            feat.Destroy()
    repack(out_ds, out_lyr)
    out_ds.Destroy()
    return


def spatial_join(polygons, points, output, fields, mode='majority', count_field=None, overwrite=False):
    # type: (str, str, str, list or tuple, str, str, bool) -> None
    """
    Join attributes from a point vector file to a polygon vector file. Attributes need to have
    different field names!

    :param polygons: Path to polygon vector file
    :param points: Path to point vector file
    :param output: Path to output file
    :param fields: List of field names that shall be joined. May also be a string if only one field shall be used.
    :param mode: Join mode in case more than one point is contained in the same polygon. Choices are: <br>
        - first: first occurrence, based on FID <br>
        - majority: most common value of attribute column "count_field" <br>
        - minority: least common value of attribute column "count_field" <br>
        In case of a tie between most/least common values, the first occurrence is used (usually the first element in
        ascending order).
    :param count_field: Field on which the modes "majority" and "minority" are based on. If None, the first entry
        from parameter "fields" is used.
    :param overwrite: Overwrite the output file in case it already exists.
    :return: --
    """
    print('Checking inputs...')
    if not os.path.exists(polygons) or not os.path.exists(points):
        raise IOError('Input files do not exist!')
    if mode.lower() not in ('first', 'minority', 'majority'):
        raise ValueError('Mode must be "first", "minority" or "majority"')
    if not count_field:
        count_field = fields[0]
    if not isinstance(fields, list):
        fields = [fields]
    copy_ds(polygons, output, overwrite)
    out_ds = ogr.Open(output, 1)
    out_lyr = out_ds.GetLayer()
    out_lyr_defn = out_lyr.GetLayerDefn()
    out_fieldnames = [out_lyr_defn.GetFieldDefn(f).name.lower() for f in range(out_lyr_defn.GetFieldCount())]
    point_ds = ogr.Open(points, 0)
    point_lyr = point_ds.GetLayer()
    point_defn = point_lyr.GetLayerDefn()
    point_fieldnames = [point_defn.GetFieldDefn(f).name.lower() for f in range(point_defn.GetFieldCount())]
    if count_field.lower() not in point_fieldnames:
        point_ds.Destroy()
        out_ds.Destroy()
        delete_ds(output)
        raise KeyError('Desired "count_field" {f} does not exist!'.format(f=count_field))
    print('Creating new fields...')
    for f, field_name in enumerate(fields):
        f_index = point_lyr.FindFieldIndex(field_name, 1)
        if f_index < 0:
            out_ds.Destroy()
            point_ds.Destroy()
            delete_ds(output)
            raise KeyError('Desired field {f} does not exist!'.format(f=field_name))
        if field_name.lower() in out_fieldnames:
            warnings.warn('WARNING: Field name {f} already exists! It will be adjusted automatically!'.format(
                f=field_name))
        out_lyr.CreateField(point_defn.GetFieldDefn(f_index))
    print('Joining points...')
    for fid in tqdm(range(out_lyr.GetFeatureCount()), desc='Progress:'):
        segment = out_lyr.GetFeature(fid)
        poly = segment.GetGeometryRef()
        point_dict = dict()
        out_feat = None
        for p in range(point_lyr.GetFeatureCount()):
            dot = point_lyr.GetFeature(p)
            point = dot.GetGeometryRef()
            if point.Within(poly):
                match_point = dot.Clone()
                point_dict[match_point.GetFID()] = match_point
                if mode == 'first':
                    out_feat = segment.Clone()
                    out_point = match_point
                    break
            else:
                continue
        if len(point_dict.keys()) > 0:
            majority_counter = Counter([point_dict[key].GetField(count_field) for key in point_dict.keys()])
            if mode == 'majority':
                value, count = majority_counter.most_common()[0]
            else:
                value, count = majority_counter.most_common()[-1]
            for key in point_dict.keys():
                if point_dict[key].GetField(count_field) == value:
                    out_feat = segment.Clone()
                    out_point = point_dict[key]
                    break
                else:
                    continue
        if out_feat:
            for field in fields:
                segment.SetField(field, out_point.GetField(field))
                out_lyr.SetFeature(segment)
        else:
            out_lyr.DeleteFeature(segment.GetFID())
    repack(out_ds, out_lyr)
    out_ds.Destroy()
    point_ds.Destroy()
    return


def intersect(files, output, overwrite=True):
    # type: (list or tuple, str, bool) -> None
    """
    Intersect vector files (assuming they share the same coordinate system)

    :param files: List of input files of the same geometry type (e.g. all polygons)
    :param output: Output file
    :param overwrite: Overwrite output, if it already exists
    :return: --
    """
    geom_types = []
    for f in files:
        ds = ogr.Open(f)
        lyr = ds.GetLayer()
        geom_types.append(lyr.GetGeomType())
        ds.Destroy()
    if len(set(geom_types)) != 1:
        raise AttributeError('Input files have different geometry types!')
    # initiate output
    if os.path.exists(output) and overwrite is True:
        delete_ds(output)
    elif os.path.exists(output) and overwrite is False:
        raise ValueError('Output file {out} already exists and shall not be overwritten! Please choose another name or '
                         'set overwrite=True.'.format(out=output))
    ds = ogr.Open(files[0])
    lyr = ds.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    drv = ds.GetDriver()
    ds.Destroy()
    out_ds, out_lyr = create_ds(output, drv.GetName(), geom_types[0], srs)
    # intersect
    intersection = ogr.Geometry(geom_types[0])
    for f in files:
        ds = ogr.Open(f)
        lyr = ds.GetLayer()
        for feature in range(lyr.GetFeatureCount()):
            feat = lyr.GetFeature(feature)
            if intersection.IsEmpty() is True:
                intersection = intersection.Union(feat.GetGeometryRef())
            else:
                intersection = intersection.Intersection(feat.GetGeometryRef())
            feat.Destroy()
        ds.Destroy()
    featureDefn = out_lyr.GetLayerDefn()
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(intersection)
    out_lyr.CreateFeature(feature)
    feature.Destroy()
    repack(out_ds, out_lyr)
    out_ds.Destroy()
    return


def buffer(ds_name, dist, output, overwrite):
    # type: (str, int or float, str, bool) -> None
    """
    Buffer a vector file by a given distance

    :param ds_name: Input file
    :param dist: Buffer distance in map units (as defined within the spatial reference)
    :param output: Output file
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    ds = ogr.Open(ds_name, 0)
    lyr = ds.GetLayer()
    drv = ds.GetDriver()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    out_ds, out_lyr = create_ds(output, drv.GetName(), lyr.GetGeomType(), srs, overwrite)
    defn = out_lyr.GetLayerDefn()
    for feat in lyr:
        geom = feat.GetGeometryRef()
        geom_buff = geom.Buffer(dist)
        out_feat = ogr.Feature(defn)
        out_feat.SetGeometry(geom_buff)
        out_lyr.CreateFeature(out_feat)
    ds.Destroy()
    repack(out_ds, out_lyr)
    out_ds.Destroy()
    return


def simplify(ds_name, tolerance, output, overwrite=False):
    # type: (str, int or float, str, bool) -> None
    """
    Simplify the geometries of a vector file within a given distance tolerance

    :param ds_name: Input filename
    :param tolerance: Distance tolerance for simplification
    :param output: Output filename
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    ds = ogr.Open(ds_name, 0)
    lyr = ds.GetLayer()
    out_ds, out_lyr = create_ds(output, ds.GetDriver().GetName(), lyr.GetGeomType(), lyr.GetSpatialRef(), overwrite)
    defn = out_lyr.GetLayerDefn()
    for feat in lyr:
        geom = feat.GetGeometryRef()
        geom_buff = geom.Simplify(tolerance)
        out_feat = ogr.Feature(defn)
        out_feat.SetGeometry(geom_buff)
        out_lyr.CreateFeature(out_feat)
    ds.Destroy()
    repack(out_ds, out_lyr)
    out_ds.Destroy()
    return


def dissolve(ds_name, output, multipoly=False, overwrite=False):
    # type: (str, str, bool, bool) -> None
    """
    Dissolve a vector file

    :param ds_name: Input filename
    :param output: Output filename
    :param multipoly: True for multipart polygon, False for many singlepart polygons
    :param overwrite: Overwrite output file, if it already exists
    :return: --
    """
    ds = ogr.Open(ds_name, 0)
    lyr = ds.GetLayer()
    out_ds, out_lyr = create_ds(output, ds.GetDriver().GetName(), lyr.GetGeomType(), lyr.GetSpatialRef(), overwrite)
    defn = out_lyr.GetLayerDefn()
    multi = ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in lyr:
        if feat.geometry():
            feat.geometry().CloseRings()
            wkt = feat.geometry().ExportToWkt()
            multi.AddGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    union = multi.UnionCascaded()
    if multipoly is True:
        for geom in union:
            poly = ogr.CreateGeometryFromWkb(geom.ExportToWkb())
            feat = ogr.Feature(defn)
            feat.SetGeometry(poly)
            out_lyr.CreateFeature(feat)
    else:
        out_feat = ogr.Feature(defn)
        out_feat.SetGeometry(union)
        out_lyr.CreateFeature(out_feat)
        out_ds.Destroy()
    repack(out_ds, out_lyr)
    ds.Destroy()
    return


def get_unique_attributes(ds_name, field, show=False):
    # type: (str, str, bool) -> dict
    """
    Return a dictionary of unique attribute values for the given attribute field and their respective occurrence counts

    :param ds_name: Input dataset
    :param field: Attribute field
    :param show: Print result
    :return: Dictionary of unique values as keys and their respective counts as values
    """
    ds = ogr.Open(ds_name, 0)
    lyr = ds.GetLayer()
    if lyr.FindFieldIndex(field, 1) < 0:
        raise AttributeError('Desired field {f} does not exist!'.format(f=field))
    attributes = [f.GetField(field) for f in lyr]
    out_dict = dict(Counter(attributes))
    if show is True:
        print('Total number of features: {n}'.format(n=len(attributes)))
        print(string.join(['Attribute', '\t', 'Count', '\n'], sep=''))
        for k in sorted(out_dict.keys()):
            print k, '\t', out_dict[k]
    return out_dict


def attribute_mapping(ds_name, field, map_field, show=False):
    # type: (str, str, str, bool) -> dict
    """
    Get a dictionary of attributes and the corresponding attribute for each feature

    :param ds_name: Input file
    :param field: Main attribute field
    :param map_field: Secondary attribute field
    :param show: Print out dictionary
    :return: Dictionary of mapped attributes
    """
    ds = ogr.Open(ds_name, 0)
    lyr = ds.GetLayer()
    if lyr.FindFieldIndex(field, 1) < 0 or lyr.FindFieldIndex(map_field, 1) < 0:
        raise AttributeError('Desired field {f} does not exist!'.format(f=field))
    out_dict = {}
    for feature in lyr:
        key = str(feature.GetField(field))
        value = feature.GetField(map_field)
        if key not in out_dict.keys():
            out_dict[key] = value
    if show is True:
        print 'Attribute', '\t', 'Mapped Value', '\n'
        for k in sorted(out_dict.keys()):
            print k, '\t', out_dict[k]
    return out_dict
