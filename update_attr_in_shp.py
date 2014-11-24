# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 14:34:03 2014

@author: Hendrik
"""

### update attributes of shapefiles ###

from osgeo import ogr
import os

# open shapefile:
print 'Reading data...'

data = 'SHAPEFILE.shp'

driver = ogr.GetDriverByName('ESRI Shapefile')
# open file with read- and wright-rights and get layer:
shp = driver.Open(data, 1)
lyr = shp.GetLayer()

# get all features and apply changes:

print 'applying changes...'

field = 'FIELDNAME'

for i in range(lyr.GetFeatureCount()):
    # get feature:
    feat = lyr.GetFeature(i)
    # change attributes:    
    if feat.GetField(field) == 'OLD':
       feat.SetField(field, 'NEW')

    lyr.SetFeature(feat)
    feat = None
    
print 'Done!'

shp = None 
