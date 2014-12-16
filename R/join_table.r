library(rgdal)

# read data to join with shapefile (e.g. from csv)
csv <- SOME_TABLE
# get column names:
colnames(csv) <- head
# read shapefile to which the data will be joined:
shp <- readOGR("SHAPEFILE.shp", "SHAPEFILE")
# merge table and shapefile based on common attribute:
outShp <- merge(shp, csv, by.x="SHAPE_COLUMN", by.y="TABLE_COLUMN")
# write new shapefile:
writeOGR(outShp, "OUT_NAME.shp", "OUT_NAME", "ESRI Shapefile")
