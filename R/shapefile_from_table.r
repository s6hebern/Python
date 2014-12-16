library(rgdal)

#read data (e.g. from csv):
data <- SOME_TABLE
# apply column names:
colnames(data) <- COLNAMES
# make spatial dataset from data with xy-coordinates and define projection using EPSG:
outShp <- SpatialPointsDataFrame(X_COL, Y_COL, data=data, proj4string=CRS("+init=epsg:EPSG_CODE"))
# write shapefile:
writeOGR(outShp, "OUT_NAME.shp", "OUT_NAME", "ESRI Shapefile")
