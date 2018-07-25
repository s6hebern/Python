import os
from osgeo import ogr, osr


def createDS(ds_name, ds_format, geom_type, srs, overwrite=False):
    """
    Create an OGR Dataset and Layer. Remember to call ds.Destroy() after you finished editing it!

    :param str ds_name: Output filename.
    :param str ds_format: File format.
    :param object geom_type: OGR Geometry Type
    :param object srs: OSR Spatial Reference Object
    :param bool overwrite: Overwrite output file, if it already exists
    :return: (OGR Dataset, OGR Layer)
    :rtype: tuple
    """

    drv = ogr.GetDriverByName(ds_format)
    if os.path.exists(ds_name) and overwrite is True:
        deleteDS(ds_name)
    ds = drv.CreateDataSource(ds_name)
    lyr_name = os.path.splitext(os.path.basename(ds_name))[0]
    lyr = ds.CreateLayer(lyr_name, srs, geom_type)
    return ds, lyr


def deleteDS(ds_name):
    """
    Delete an OGR Dataset

    :param str ds_name: File to delete.
    :return: --
    """

    ds = ogr.Open(ds_name)
    drv = ds.GetDriver()
    ds.Destroy()
    drv.DeleteDataSource(ds_name)
    return True


def copyDS(src, dst):
    """
    Copy a vector file

    :param str src: Source filename
    :param str dst: Destination filename
    :return: --
    """

    if os.path.exists(dst):
        deleteDS(dst)
    ds = ogr.Open(src)
    drv = ds.GetDriver()
    out_ds = drv.CopyDataSource(ds, dst)
    out_ds.Destroy()
    ds.Destroy()
    return True


def repack(ds, lyr):
    """
    Flush pending changes on the layer and repack the file to make everything permanent

    :param OGR Dataset ds: Input OGR Dataset
    :param OGR LayerShadow lyr: OGR LayerShadow from ds
    :return: --
    """

    lyr.SyncToDisc()
    ds.ExecuteSQL('REPACK {n}'.format(n=lyr.GetName()))
    return True


def getExtent(input):
    """
    Get maximum the extent of an OGR Dataset

    :param str input: Input filename
    :return: Extent as a tuple of (xmin, ymin, xmax, ymax)
    :rtype tuple
    """

    ds = ogr.Open(input)
    lyr = ds.GetLayer(os.path.split(os.path.splitext(input)[0])[1])
    ulx, lrx, uly, lry = lyr.GetExtent()
    ds.Destroy()
    return ulx, uly, lrx, lry


def merge(files, output, overwrite=True):
    """
    Merge vector files (assuming they share the same coordinate system)

    :param list files: List of input files of the same geometry type (e.g. all polygons)
    :param str output: Output file
    :param bool overwrite: Overwrite output, if it already exists
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
        deleteDS(output)
    elif os.path.exists(output) and overwrite is False:
        raise ValueError('Output file {out} already exists and shall not be overwritten! Please choose another name or '
                         'set overwrite=True.'.format(out=output))
    ds = ogr.Open(files[0])
    lyr = ds.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    drv = ds.GetDriver()
    ds.Destroy()
    out_ds, out_lyr = createDS(output, drv.GetName(), geom_types[0], srs)
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
    return True


def intersect(files, output, overwrite=True):
    """
    Intersect vector files (assuming they share the same coordinate system)

    :param list files: List of input files of the same geometry type (e.g. all polygons)
    :param str output: Output file
    :param bool overwrite: Overwrite output, if it already exists
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
        deleteDS(output)
    elif os.path.exists(output) and overwrite is False:
        raise ValueError('Output file {out} already exists and shall not be overwritten! Please choose another name or '
                         'set overwrite=True.'.format(out=output))
    ds = ogr.Open(files[0])
    lyr = ds.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    drv = ds.GetDriver()
    ds.Destroy()
    out_ds, out_lyr = createDS(output, drv.GetName(), geom_types[0], srs)
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
    return True


def buffer(input, dist, output, overwrite):
    """
    Buffer a vector file by a given distance

    :param str input: Input file
    :param real dist: Buffer distance in map units (as defined within the spatial reference)
    :param str output: Output file
    :param bool overwrite: Overwrite output file, if it already exists
    :return: --
    """

    ds = ogr.Open(input)
    lyr = ds.GetLayer()
    drv = ds.GetDriver()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(lyr.GetSpatialRef().ExportToWkt())
    out_ds, out_lyr = createDS(output, drv.GetName(), lyr.GetGeomType(), srs, overwrite)
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
    return True


def simplify(input, tolerance, output, overwrite=False):
    """
    Simplify the geometries of a vector file within a given distance tolerance

    :param str input: Input filename
    :param numeric tolerance: Distance tolerance for simplification
    :param str output: Output filename
    :param bool overwrite: Overwrite output file, if it already exists
    :return: --
    """

    ds = ogr.Open(input)
    lyr = ds.GetLayer()
    out_ds, out_lyr = createDS(output, ds.GetDriver().GetName(), lyr.GetGeomType(), lyr.GetSpatialRef(), overwrite)
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
    return True


def dissolve(input, output, multipoly=False, overwrite=False):
    """
    Dissolve a vector file

    :param str input: Input filename
    :param str output: Output filename
    :param bool multipoly: True, if a MultiPolygon shall be created, False for single polygons
    :param bool overwrite: Overwrite output file, if it already exists
    :return: --
    """

    ds = ogr.Open(input)
    lyr = ds.GetLayer()
    out_ds, out_lyr = createDS(output, ds.GetDriver().GetName(), lyr.GetGeomType(), lyr.GetSpatialRef(), overwrite)
    defn = out_lyr.GetLayerDefn()
    multi = ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in lyr:
        if feat.geometry():
            feat.geometry().CloseRings()
            wkt = feat.geometry().ExportToWkt()
            multi.AddGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    union = multi.UnionCascaded()
    if multipoly is False:
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
    return True
