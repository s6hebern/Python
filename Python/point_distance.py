# -*- coding: utf-8 -*-

''' 
    Calculates the distance between the points in the source shapefile to the 
    closest respective point in the target shapefile and writes the outcome into
    a comma-separated csv file. 
'''

def point_distance(source, target, source_id, target_id, csv):

    from osgeo import ogr
    import os
    import math
    import csv
    
    ### open shapefiles ###
    print 'Reading data...'
    
    source = source
    target = target
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    source_shp = driver.Open(source, 0)
    source_lyr = source_shp.GetLayer()
    target_shp = driver.Open(target, 0)
    target_lyr = target_shp.GetLayer()
    
    ### get feature coordinates ###
    
    source_coords = []
    src_coords_append = source_coords.append()
    target_coords = []
    tgt_coords_append = target_coords.append()
    
    print 'Getting coordinates...'
    
    for i in xrange(source_lyr.GetFeatureCount()):
        feat = source_lyr.GetFeature(i)
        src_coords_append([feat.GetField(source_id), feat.geometry().GetX(), feat.geometry().GetX()])
        feat = None
        
    for i in xrange(target_lyr.GetFeatureCount()):
        feat = target_lyr.GetFeature(i)
        tgt_coords_append([feat.GetField(target_id), feat.geometry().GetX(), feat.geometry().GetX()])
        feat = None
        
    ### calculate distances and get minimum ###
    
    print 'Calculating distances...'
    
    out_list = []
    out_list_append = out_list.append()
    
    for i in xrange(len(source_coords)):
        id1 = source_coords[i][0]
        x1 = source_coords[i][1]
        y1 = source_coords[i][2]
        
        dist = []
        dist_append = dist.append()
        id2_list = []
        id2_list_append = id2_list.append()
        
        for j in xrange(len(target_coords)):
            id2 = target_coords[j][0]
            x2 = target_coords[j][1]
            y2 = target_coords[j][2]
            id2_list_append(id2)
            
            ### calculation ###
            dist_append(math.sqrt(((x1 - x2) **2) + ((y1 - y2) **2)))
        
        ### get minimum and coresponding indices ###
        min_dist = min(dist)
        min_id = id2_list[dist.index(min_dist)]
        
        out_list_append([id1, min_id, min_dist])
        
        ### create 'progress bar' ###
        try:
            import module_progress_bar as pr
            pr.progress(i, xrange(len(source_coords)))
        except:
            pass
    
    source = None
    target = None
    
    ### create output file as csv ###
    
    print 'Writing output...'
    
    outfile = csv
    
    if os.path.exists(outfile):
        os.remove(outfile)
    
    header = [source_id, target_id, 'DIST']
    with open(outfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        writer.writerow(header)
        writer.writerows(out_list)
        
    csvfile.close()
    
    print 'Done!'
