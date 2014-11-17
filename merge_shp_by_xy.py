# -*- coding: utf-8 -*-
"""
Created on Wed Nov 12 09:43:34 2014

@author: Hendrik
"""

### merge 3 point-shapefiles based on their xy-coordinates ###

from osgeo import ogr
import os

### open shapefiles ###
print "Reading data..."

data_2006 = r"D:\Uni\Masterarbeit\LUCAS\shapes\2006_LAEA.shp"
data_2009 = r"D:\Uni\Masterarbeit\LUCAS\shapes\2009_LAEA.shp"
data_2012 = r"D:\Uni\Masterarbeit\LUCAS\shapes\2012_LAEA.shp"

driver = ogr.GetDriverByName("ESRI Shapefile")

shp_2006 = driver.Open(data_2006, 0)
lyr_2006 = shp_2006.GetLayer()
shp_2009 = driver.Open(data_2009, 0)
lyr_2009 = shp_2009.GetLayer()
shp_2012 = driver.Open(data_2012, 0)
lyr_2012 = shp_2012.GetLayer()

### get all features ###

points_2006 = []
coords_2006 = []
points_2009 = []
coords_2009 = []
points_2012 = []
coords_2012 = []

print "Getting coordinates..."

for i in range(lyr_2006.GetFeatureCount()):
    feat = lyr_2006.GetFeature(i)
    points_2006.append(feat)
    coords_2006.append((feat.GetField("X_LAEA"), feat.GetField("Y_LAEA")))
    feat = None
    
for i in range(lyr_2009.GetFeatureCount()):
    feat = lyr_2009.GetFeature(i)
    points_2009.append(feat)
    coords_2009.append((feat.GetField("X_LAEA"), feat.GetField("Y_LAEA")))
    feat = None
    
for i in range(lyr_2012.GetFeatureCount()):
    feat = lyr_2012.GetFeature(i)
    points_2012.append(feat)
    coords_2012.append((feat.GetField("X_LAEA"), feat.GetField("Y_LAEA")))
    feat = None
    
### compare all features based on their xy-coordinates ###

match = []
LC1_2006 = []
LC2_2006 = []
LC1_2009 = []
LC2_2009 = []
LC1_2012 = []
LC2_2012 = []
LU1_2006 = []
LU2_2006 = []
LU1_2009 = []
LU2_2009 = []
LU1_2012 = []
LU2_2012 = []
DIST_2006 = []
DIST_2009 = []
DIST_2012 = []

print "Matching points and getting attributes..."

counter = 0

for i in range(len(points_2006)):
    if coords_2006[i] in coords_2009 and coords_2006[i] in coords_2012:
        match.append(points_2006[i])
        LC1_2006.append(points_2006[i].GetField("LC1"))
        LC2_2006.append(points_2006[i].GetField("LC2"))
        LU1_2006.append(points_2006[i].GetField("LU1"))
        LU2_2006.append(points_2006[i].GetField("LU2"))
        DIST_2006.append(points_2006[i].GetField("POINT_DIST"))
        
        ### get index of matching coordinate, then use this to get attribute ###
        LC1_2009.append(points_2009[coords_2009.index(coords_2006[i])].GetField("LC1"))
        LC2_2009.append(points_2009[coords_2009.index(coords_2006[i])].GetField("LC2"))
        LC1_2012.append(points_2012[coords_2012.index(coords_2006[i])].GetField("LC1"))
        LC2_2012.append(points_2012[coords_2012.index(coords_2006[i])].GetField("LC2"))
        LU1_2009.append(points_2009[coords_2009.index(coords_2006[i])].GetField("LU1"))
        LU2_2009.append(points_2009[coords_2009.index(coords_2006[i])].GetField("LU2"))
        LU1_2012.append(points_2012[coords_2012.index(coords_2006[i])].GetField("LU1"))
        LU2_2012.append(points_2012[coords_2012.index(coords_2006[i])].GetField("LU2"))
        DIST_2009.append(points_2009[coords_2009.index(coords_2006[i])].GetField("POINT_DIST"))
        DIST_2012.append(points_2012[coords_2012.index(coords_2006[i])].GetField("POINT_DIST"))
        
        ### make LC classes consistent within all 3 years ###
        if LC1_2006[counter] == "C11":
            LC1_2006[counter] = "C10"
        if LC1_2006[counter] == "C22":
            LC1_2006[counter] = "C20"
        if LC1_2006[counter] == "C21":
            LC1_2006[counter] = "C10"
        if LC1_2006[counter] == "C22":
            LC1_2006[counter] = "C10"
        if LC1_2006[counter] == "C13":
            LC1_2006[counter] = "C33"
        if LC1_2006[counter] == "C23":
            LC1_2006[counter] = "C33"
        if LC1_2009[counter] == "C30":
            LC1_2009[counter] = "C33"
        if LC1_2006[counter] == "D01":
            LC1_2006[counter] = "D10"
        if LC1_2006[counter] == "D02":
            LC1_2006[counter] = "D20"
        if LC1_2006[counter] == "E01":
            LC1_2006[counter] = "E10"
        if LC1_2006[counter] == "E02":
            LC1_2006[counter] = "E20"
        if LC1_2012[counter] == "F10":
            LC1_2012[counter] = "F00"
        if LC1_2012[counter] == "F20":
            LC1_2012[counter] = "F00"
        if LC1_2012[counter] == "F30":
            LC1_2012[counter] = "F00"
        if LC1_2012[counter] == "F40":
            LC1_2012[counter] = "F00"
        if LC1_2006[counter] == "G01":
            LC1_2006[counter] = "G10"
        if LC1_2006[counter] == "G02":
            LC1_2006[counter] = "G20"
            
        counter += 1
            
    ### create 'progress bar' ###
    if i == round(len(points_2006) * 10 / 100):
        print "... 10 % ..." ,
    if i == round(len(points_2006) * 20 / 100):
        print "20 % ..." ,
    if i == round(len(points_2006) * 30 / 100):
        print "30 % ..." ,
    if i == round(len(points_2006) * 40 / 100):
        print "40 % ..."   ,      
    if i == round(len(points_2006) * 50 / 100):
        print "50 % ..."     ,    
    if i == round(len(points_2006) * 60 / 100):
        print "60 % ..."  ,
    if i == round(len(points_2006) * 70 / 100):
        print "70 % ..." ,
    if i == round(len(points_2006) * 80 / 100):
        print "80 % ..." ,
    if i == round(len(points_2006) * 90 / 100):
        print "90 % ..." ,
    if i == len(points_2006) - 1:
        print "100 %"

### create new shapefile ###    

print "Creating output..."

newShp = r"D:\Uni\Masterarbeit\LUCAS\shapes\LUCAS_all_LAEA.shp"

if os.path.exists(newShp):
    driver.DeleteDataSource(newShp)
    
outShp = driver.CreateDataSource(newShp)
outLyr = outShp.CreateLayer("point", shp_2006.GetLayer().GetSpatialRef(), geom_type=ogr.wkbPoint)
featureDefn = outLyr.GetLayerDefn()

fieldNames = ["ID", "LC1_2006", "LC2_2006", "LC1_2009", "LC2_2009", "LC1_2012", "LC2_2012", \
            "LU1_2006", "LU2_2006", "LU1_2009", "LU2_2009", "LU1_2012", "LU2_2012", \
            "DIST_2006", "DIST_2009", "DIST_2012"]
fieldTypes = [ogr.OFTString] * 12
fieldTypes.insert(0, ogr.OFTInteger)
for j in range(3):
    fieldTypes.append(ogr.OFTReal)

### create attribute fields ###

for f in range(len(fieldNames)):
    field =  ogr.FieldDefn(fieldNames[f], fieldTypes[f])
    if fieldTypes[f] == ogr.OFTInteger or fieldTypes[f] == ogr.OFTString:
        field.SetWidth(5)
    if fieldTypes[f] == ogr.OFTReal:
        field.SetWidth(10)
        field.SetPrecision(2)
    outLyr.CreateField(field)
    field = None

### set points and attributes ###

for i in range(len(match)):
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(match[i].geometry().GetX(), match[i].geometry().GetY())
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(point)
    feature.SetField("ID", i)
    feature.SetField("LC1_2006", LC1_2006[i])
    feature.SetField("LC2_2006", LC2_2006[i])
    feature.SetField("LC1_2009", LC1_2009[i])
    feature.SetField("LC2_2009", LC2_2009[i])
    feature.SetField("LC1_2012", LC1_2012[i])
    feature.SetField("LC2_2012", LC2_2012[i])
    feature.SetField("LU1_2006", LU1_2006[i])
    feature.SetField("LU2_2006", LU2_2006[i])
    feature.SetField("LU1_2009", LU1_2009[i])
    feature.SetField("LU2_2009", LU2_2009[i])
    feature.SetField("LU1_2012", LU1_2012[i])
    feature.SetField("LU2_2012", LU2_2012[i])
    feature.SetField("DIST_2006", DIST_2006[i])
    feature.SetField("DIST_2009", DIST_2009[i])
    feature.SetField("DIST_2012", DIST_2012[i])
    outLyr.CreateFeature(feature)
    feature=None

shp_2006 = None
shp_2009 = None
shp_2012 = None   
outShp = None

print "Done!"
