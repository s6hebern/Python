# -*- coding: utf-8 -*-
'''
Created on Wed Nov 12 09:43:34 2014

@author: Hendrik
'''

""" Spatial join of two point shapefiles. Writes a new shapefile cotaining the
    common points and one attribute field from each shapefile. All function
    arguments given as strings. """

def spatial_join(shape_1, shape_2, out_shape, field_1, field_2):
    from osgeo import ogr
    import os
    
    ### open shapefiles ###
    print 'Reading data...'
    
    shape_1 = shape_1
    shape_2 = shape_2
    out_shape = out_shape
    # desired attributes to keep:
    fld_1 = field_1
    fld_2 = field_2
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    shp_1 = driver.Open(shape_1, 0)
    lyr_1 = shp_1.GetLayer()
    shp_2 = driver.Open(shape_2, 0)
    lyr_2 = shp_2.GetLayer()
    
    ### get all features ###
    
    points_1 = []
    append_p1 = points_1.append
    coords_1 = []
    append_c1 = coords_1.append
    points_2 = []
    append_p2 = points_2.append
    coords_2 = []
    append_c2 = coords_2.append
    
    print 'Getting coordinates...'
    
    for i in xrange(lyr_1.GetFeatureCount()):
        feat = lyr_1.GetFeature(i)
        append_p1(feat)
        append_c1((feat.geometry().GetX(), feat.geometry().GetY()))
        feat = None
        
    for i in xrange(lyr_2.GetFeatureCount()):
        feat = lyr_2.GetFeature(i)
        append_p2(feat)
        append_c2((feat.geometry().GetX(), feat.geometry().GetY()))
        feat = None
        
    ### compare all features based on their xy-coordinates ###
    
    match = []
    append_match = match.append
    attr_1 = []
    append_attr_1 = attr_1.append
    attr_2 = []
    append_attr_2 = attr_2.append
    
    print 'Matching points and getting attributes...'
    
    counter = 0
    
    for i in xrange(len(points_1)):
        if coords_1[i] in coords_2:
            append_match(points_1[i])
            append_attr_1(points_1[i].GetField(fld_1))
            ### get index of matching coordinate, then use this to get attribute ###
            append_attr_2(points_2[coords_2.index(coords_1[i])].GetField(fld_2))
            counter += 1
                
        ### create 'progress bar' ###
        try:
            import module_progress_bar as pr
            pr.progress(i, xrange(len(points_1)))
        except:
            pass
    
    ### create new shapefile ###    
    
    print 'Creating output...'
    
    if os.path.exists(out_shape):
        driver.DeleteDataSource(out_shape)
        
    outShp = driver.CreateDataSource(out_shape)
    outLyr = outShp.CreateLayer('point', shp_1.GetLayer().GetSpatialRef(), geom_type=ogr.wkbPoint)
    featureDefn = outLyr.GetLayerDefn()
    
    ### create attribute fields ###
    fieldNames = ['ID', fld_1, fld_2]
    fieldTypes = [points_1[0].GetFieldDefnRef(points_1[0].GetFieldIndex(fld_1)).GetType(), \
                points_2[0].GetFieldDefnRef(points_2[0].GetFieldIndex(fld_2)).GetType()]
    fieldTypes.insert(0, ogr.OFTInteger)
    
    for f in xrange(len(fieldNames)):
        field =  ogr.FieldDefn(fieldNames[f], fieldTypes[f])
        if fieldNames[f] == 'ID':
            field.SetWidth(len(str(len(points_1) + len(points_2))) + 1)
        else:
            if fieldNames[f] == fld_1:
                if fieldTypes[f] == ogr.OFTInteger or fieldTypes[f] == ogr.OFTString:
                    field.SetWidth(points_1[0].GetFieldDefnRef(points_1[0].GetFieldIndex(fld_1)).GetWidth())
                if fieldTypes[f] == ogr.OFTReal:
                    field.SetWidth(points_1[0].GetFieldRef(points_1[0].GetFieldIndex(fld_1)).GetWidth())
                    field.SetPrecision(points_1[0].GetFieldDefnRef(points_1[0].GetFieldIndex(fld_1)).GetPrecision())
            if fieldNames[f] == fld_2:
                if fieldTypes[f] == ogr.OFTInteger or fieldTypes[f] == ogr.OFTString:
                    field.SetWidth(points_2[0].GetFieldDefnRef(points_2[0].GetFieldIndex(fld_2)).GetWidth())
                if fieldTypes[f] == ogr.OFTReal:
                    field.SetWidth(points_2[0].GetFieldDefnRef(points_2[0].GetFieldIndex(fld_2)).GetWidth())
                    field.SetPrecision(points_2[0].GetFieldDefnRef(points_2[0].GetFieldIndex(fld_2)).GetPrecision())
        # create the field:
        outLyr.CreateField(field)
        field = None
    
    ### set points and attributes ###
    
    for i in xrange(len(match)):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(match[i].geometry().GetX(), match[i].geometry().GetY())
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(point)
        feature.SetField('ID', i)
        feature.SetField(fld_1, attr_1[i])
    
        feature.SetField(fld_2, attr_2[i])
    
        outLyr.CreateFeature(feature)
        feature=None
    
    shp_1 = None
    shp_2 = None   
    outShp = None
    
    print 'Done!'
