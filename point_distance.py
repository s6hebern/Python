# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 11:21:48 2014

@author: Hendrik
"""

### get distance between source point shapefile and closest point in target shapefile ###

from osgeo import ogr
import os
import csv

### open shapefiles ###
print "Reading data..."

source = r"D:\Uni\Masterarbeit\shapes\stations_germany_landuse.shp"
target = r"D:\Uni\Masterarbeit\LUCAS\shapes\LUCAS_all_WGS84_lu.shp"

driver = ogr.GetDriverByName("ESRI Shapefile")

source_shp = driver.Open(source, 0)
source_lyr = source_shp.GetLayer()
target_shp = driver.Open(target, 0)
target_lyr = target_shp.GetLayer()

### get feature coordinates ###

source_coords = []
target_coords = []

print "Getting coordinates..."

for i in range(source_lyr.GetFeatureCount()):
    feat = source_lyr.GetFeature(i)
    source_coords.append([feat.GetField("Stations_i"), feat.GetField("X"), feat.GetField("Y")])
    
for i in range(target_lyr.GetFeatureCount()):
    feat = target_lyr.GetFeature(i)
    target_coords.append([feat.GetField("ID"), feat.GetField("X"), feat.GetField("Y")])
    
### calculate distances and get minimum ###

print "Calculating distances..."

out_list = []

for i in range(len(source_coords)):
    id1 = source_coords[i][0]
    x1 = source_coords[i][1]
    y1 = source_coords[i][2]
    
    dist = []
    id2_list = []
    
    for j in range(len(target_coords)):
        id2 = target_coords[j][0]
        x2 = target_coords[j][1]
        y2 = target_coords[j][2]
        id2_list.append(id2)
        
        ### calculation ###
        dist.append(sqrt(((x1 - x2) **2) + ((y1 - y2) **2)))
    
    ### get minimum and coresponding indices ###
    min_dist = min(dist)
    min_id = id2_list[dist.index(min(dist))]
    
    out_list.append([id1, min_id, min_dist])
    
    ### create 'progress bar' ###
    if i == round(len(source_coords) * 10 / 100):
        print "... 10 % ..." ,
    if i == round(len(source_coords) * 20 / 100):
        print "20 % ..." ,
    if i == round(len(source_coords) * 30 / 100):
        print "30 % ..." ,
    if i == round(len(source_coords) * 40 / 100):
        print "40 % ..."   ,      
    if i == round(len(source_coords) * 50 / 100):
        print "50 % ..."     ,    
    if i == round(len(source_coords) * 60 / 100):
        print "60 % ..."  ,
    if i == round(len(source_coords) * 70 / 100):
        print "70 % ..." ,
    if i == round(len(source_coords) * 80 / 100):
        print "80 % ..." ,
    if i == round(len(source_coords) * 90 / 100):
        print "90 % ..." ,
    if i == len(source_coords) - 1:
        print "100 %"

source = None
target = None

### create output file as csv ###

print "Writing output..."

outfile = r"D:\Uni\Masterarbeit\min_dist_phen_LUCAS.csv"

if os.path.exists(outfile):
    os.remove(outfile)

header = ["STATION_ID", "LUCAS_ID", "DIST"]
with open(outfile, 'wb') as csvfile:
    writer = csv.writer(csvfile, delimiter = ',')
    writer.writerow(header)
    writer.writerows(out_list)
    
csvfile.close()

print "Done!"
