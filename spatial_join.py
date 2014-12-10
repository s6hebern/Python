# -*- coding: utf-8 -*-
"""
Created on Fri Dec 05 13:45:23 2014

@author: Hendrik
"""

""" 
    Spatial join oftwo or more point shapefiles. Writes a new shapefile
    cotaining the common points and one attribute field from each shapefile. 
    
    Use:
    
    shapes: a LIST of the input shapefiles, given as strings (full path and 
            file extension).
            
    out_shape: the name of the output shapefile (full path and file extension).
    
    fields: a LIST of the desired attribute fields to keep, given as strings, in
            the same order as the inout shapefiles. If more than one field shall
            be kept, use a TUPLE of strings for the respective shapefile. If not
            set, no attribute fields will be written except for an ID field.
            
    out_fields: a LIST of names for the desired output attribute fields. If not
            set, field names will be the same as in the input shapefiles (which
            may be confusing, if field names are the same in two or more 
            shapefiles).
"""

def spatial_join(shapes, out_shape, fields = None, out_fields = None):
    from osgeo import ogr
#    import collections as coll
    import os
    try:
        import module_progress_bar as pr
    except:
        pass
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    points = []
    points_append = points.append
    coords = []
    coords_append = coords.append
    
    # get all points and their coordinates using lists in lists:
    print 'Getting coordinates ...'
    
    for shape in xrange(len(shapes)):
        shp = driver.Open(shapes[shape], 0)
        lyr = shp.GetLayer()
        points_append([])
        pts_append = points[shape].append
        coords_append([])
        crds_append = coords[shape].append
    
        for i in xrange(lyr.GetFeatureCount()):
            feat = lyr.GetFeature(i)
            pts_append(feat)
            crds_append((feat.geometry().GetX(), feat.geometry().GetY()))
            feat = None
            
    # find matching points:
    print 'Matching coordinates ...'
    match = []
    match_append = match.append
    
    for shape in xrange(len(shapes)):
        if shape < len(shapes) - 1:
            print 'Pair', shape + 1, 'of', str(len(shapes)-1) + ':'
            for pt in xrange(len(points[shape])):
                if coords[shape][pt] in \
                    coords[shape + 1][0:len(coords[shape + 1])]:
                    match_append((points[shape][pt].geometry().GetX(), \
                        points[shape][pt].geometry().GetY()))
                            
                try:
                    pr.progress(pt, xrange(len(points[shape])))
                except:
                    pass
    
    # 'match' contains all points which can be found in at least two files
    # (meaning one combination) -> only points which occur in all files are kept:
    print 'Cleaning up matching coordinates ...'
    
    match = list(set([m for m in match if match.count(m) == len(shapes) - 1]))

    # get attributes:
    attr = []
    attr_append = attr.append
    counter = 0
    print 'Getting attributes ...'
    
    for shape in xrange(len(shapes)):        
        if fields == None:
            print 'No attribute fields set by input ...'
            attr_append([])
            at_append = attr[counter].append
            
            for pt in xrange(len(points[shape])):
                p = (points[shape][pt].geometry().GetX(), \
                    points[shape][pt].geometry().GetY())
                if p in match:
                        at_append((match[match.index(p)]))
                        
            break
        
        else:
            print 'Shape', shape + 1, 'of', len(shapes)
            
            if type(fields[shape]) == str:
                #print 'Field 1 of 1'
                attr_append([])
                at_append = attr[counter].append
                
                counter += 1
                
                for pt in xrange(len(points[shape])):
                    p = (points[shape][pt].geometry().GetX(), \
                        points[shape][pt].geometry().GetY())
                    if p in match:
                        at_append((match[match.index(p)], points[shape][pt].GetField(fields[shape])))
                        
                    try:
                        pr.progress(pt, xrange(len(points[shape])))
                    except:
                        pass
    
            else:
                for fld in xrange(len(fields[shape])):
                    #print 'Field', fld + 1, 'of', len(fields[shape])
                    attr_append([])
                    at_append = attr[counter].append
                    
                    counter += 1
                    
                    for pt in xrange(len(points[shape])):
                        p = (points[shape][pt].geometry().GetX(), \
                            points[shape][pt].geometry().GetY())
                        if p in match:
                            at_append((match[match.index(p)], points[shape][pt].GetField(fields[shape][fld])))
    
    sort = [sorted(i) for i in attr]
    attr = sort
    
    # create output shapefile:
    print 'Creating output...'
    
    if os.path.exists(out_shape):
        driver.DeleteDataSource(out_shape)
    
    outShp = driver.CreateDataSource(out_shape)
    outLyr = outShp.CreateLayer('point', shp.GetLayer().GetSpatialRef(), geom_type=ogr.wkbPoint)
    featureDefn = outLyr.GetLayerDefn()
    
    # define new attribute fields (including a new ID field):
    fieldNames = []
    fldNam_append = fieldNames.append
    fieldTypes = []
    fldTyp_append = fieldTypes.append
    fieldWidth = []
    fldWid_append = fieldWidth.append
    fieldPrec = []
    fldPrec_append = fieldPrec.append
    
    if out_fields == None:
        if  fields != None:
            # define field names and types from input fields        
            for shape in xrange(len(shapes)):
                # check if only one attribute field is desired:
                if type(fields[shape]) == str:
                    fldNam_append(fields[shape])
                    fldTyp_append(points[shape][0].GetFieldDefnRef(points[shape] \
                        [0].GetFieldIndex(fields[shape])).GetType())
                    fldWid_append(points[shape][0].GetFieldDefnRef(points[shape] \
                            [0].GetFieldIndex(fields[shape])).GetWidth())
                    # check if field is of type REAL and get precision:
                    if points[shape][0].GetFieldDefnRef(points[shape][0] \
                        .GetFieldIndex(fields[shape])).GetType() \
                        == ogr.OFTReal:
                            fldPrec_append(points[shape][0].GetFieldDefnRef \
                            (points[shape][0].GetFieldIndex(fields[shape])) \
                            .GetPrecision())
                    else:
                        fldPrec_append(None)
                        
                else:
                    for fld in xrange(len(fields[shape])):
                        fldNam_append(fields[shape][fld])
                        fldTyp_append(points[shape][0].GetFieldDefnRef(points[shape] \
                            [0].GetFieldIndex(fields[shape][fld])).GetType())
                        fldWid_append(points[shape][0].GetFieldDefnRef(points[shape] \
                            [0].GetFieldIndex(fields[shape][fld])).GetWidth())
                        # check if field is of type REAL and get precision:
                        if points[shape][0].GetFieldDefnRef(points[shape][0] \
                            .GetFieldIndex(fields[shape][fld])).GetType() \
                            == ogr.OFTReal:
                                fldPrec_append(points[shape][0].GetFieldDefnRef \
                                (points[shape][0].GetFieldIndex(fields[shape][fld])) \
                                .GetPrecision())
                        else:
                            fldPrec_append(None)
                            
        fieldNames.insert(0, 'ID')
        fieldTypes.insert(0, ogr.OFTInteger)
        fieldWidth.insert(0, len(str(len(match) + 1)))
        fieldPrec.insert(0, None)
        
    else:
        # take given field names, define field types from input fields:
        fieldNames = out_fields
        for shape in xrange(len(shapes)):
            # check if only one attribute field is desired:
            if type(fields[shape]) == str:
                fldTyp_append(points[shape][0].GetFieldDefnRef(points[shape] \
                    [0].GetFieldIndex(fields[shape])).GetType())
                fldWid_append(points[shape][0].GetFieldDefnRef(points[shape] \
                    [0].GetFieldIndex(fields[shape])).GetWidth())
                # check if field is of type REAL and get precision:
                if points[shape][0].GetFieldDefnRef(points[shape][0] \
                    .GetFieldIndex(fields[shape])).GetType() \
                    == ogr.OFTReal:
                        fldPrec_append(points[shape][0].GetFieldDefnRef \
                        (points[shape][0].GetFieldIndex(fields[shape])) \
                        .GetPrecision())
                else:
                    fldPrec_append(None)
                    
            else:
                for fld in xrange(len(fields[shape])):
                    fldNam_append(fields[shape][fld])
                    fldTyp_append(points[shape][0].GetFieldDefnRef(points[shape] \
                        [0].GetFieldIndex(fields[shape][fld])).GetType())
                    fldWid_append(points[shape][0].GetFieldDefnRef(points[shape] \
                        [0].GetFieldIndex(fields[shape][fld])).GetWidth())
                    # check if field is of type REAL and get precision:
                    if points[shape][0].GetFieldDefnRef(points[shape][0] \
                        .GetFieldIndex(fields[shape][fld])).GetType() \
                        == ogr.OFTReal:
                            fldPrec_append(points[shape][0].GetFieldDefnRef \
                            (points[shape][0].GetFieldIndex(fields[shape][fld])) \
                            .GetPrecision())
                    else:
                        fldPrec_append(None)
                        
        fieldNames.insert(0, 'ID')
        fieldTypes.insert(0, ogr.OFTInteger)
        fieldWidth.insert(0, len(str(len(match) + 1)))
        fieldPrec.insert(0, None)

    # create attribute fields in output shapefile:
    for f in xrange(len(fieldNames)):
        field =  ogr.FieldDefn(fieldNames[f], fieldTypes[f])
        field.SetWidth(fieldWidth[f])
        
        if fieldTypes[f] == ogr.OFTReal:
            field.SetPrecision(fieldPrec[f])
            
        outLyr.CreateField(field)
        field = None

    for i in xrange(len(match)):
        point = ogr.Geometry(ogr.wkbPoint)
        if fields != None:
            point.AddPoint(attr[0][i][0][0], attr[0][i][0][1])
        else:
            point.AddPoint(attr[0][i][0], attr[0][i][1])
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(point)
        feature.SetField('ID', i)
        
        if fields != None:
            for f in xrange(1, len(fieldNames)):
                feature.SetField(fieldNames[f], attr[f - 1][i][1])
    
        outLyr.CreateFeature(feature)
        feature = None
            
        try:
            pr.progress(i, xrange(len(match)))
        except:
            pass

    shp = None
    outShp = None
