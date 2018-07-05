import os
from osgeo import ogr, osr

def merge(files, output, overwrite=True):
    """
    Merge vector files (assuming they share the same coordinate system)

    :param list files: List of input files of the same geometry type (e.g. all polygons)
    :param str output: Output file
    :param bool overwrite: Overwrite output, if it already exists
    :return: --
    """
    # check geometry types
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
    out_ds.Destroy()


def intersect(files, output, overwrite=True):
    """
    Intersect vector files (assuming they share the same coordinate system)

    :param list files: List of input files of the same geometry type (e.g. all polygons)
    :param str output: Output file
    :param bool overwrite: Overwrite output, if it already exists
    :return: --
    """
    # check geometry types
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
    out_ds.Destroy()


def createDS(ds_name, ds_format, geom_type, srs):
    drv = ogr.GetDriverByName(ds_format)
    ds = drv.CreateDataSource(ds_name)
    lyr_name = os.path.splitext(os.path.basename(ds_name))[0]
    lyr = ds.CreateLayer(lyr_name, srs, geom_type)
    return ds, lyr


def deleteDS(ds_name):
    ds = ogr.Open(ds_name)
    drv = ds.GetDriver()
    ds.Destroy()
    drv.DeleteDataSource(ds_name)
    drv = None
