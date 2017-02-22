README

This function was designed to create a regular grid of point coordinates, with 
the flexibility to handle different coordinate systems (CRS).

Usage:
regularGridPoints(xmin, ymin, xmax, ymax, stepx, stepy, out, epsgIn="4326", stepDeg=F, epsgOut="4326")

Parameters:
xmin	(numeric)	-> x-coordinate of lower left corner
ymin 	(numeric)	-> y-coordinate of lower left corner
xmax	(numeric)	-> x-coorcinate of upper right corner
ymax	(numeric)	-> y-coordinate of upper right corner
stepx	(numeric)	-> horizontal distance between points
stepy	(numeric)	-> vertical distance between point
out 	(string)	-> output file as csv (full path and file extension)
epsgIn	(string)	-> EPSG-code of input coordinates (defaults to geographic WGS84)
stepDeg	(boolean)	-> boolean indicator whether the distances between points are 
			given in degrees (TRUE) or meters (FALSE). Must not be 
			FALSE if in-and output CRS are both "4326"
epsgOut	(string)	-> EPSG-code of output coordinates (defaults to geographic WGS84)

Important notes:
- If the distance between points is given in meters, but the output CRS is 
	"4326", an internal transformation of the input points to UTM will
	take place. Based on that, the number of output points will be calculated.
	Then, the distance between xmin/max and ymin/ymax will be splitted into this
	many segments. By this, the metric distance is turned into a distance in 
	degrees, which equals the metric distance only at the grid's lower left 
	corner. Therefore, the metric horizontal distance between points decreases
	the further you move up (north).
	This leads to a different distance between points
	than given in stepx/stepy! This can only be avoided by using a metric CRS
	for output.
- The output file will always be a comma-separated csv-file, containing only
	an ID-column, followed by the columns for x- and y-coordinates.

Examples:
# geographic coordinates as in- and output, distance between points in meters
test <- "C:/test_all_geo.csv"
regularGridPoints(5, 45, 10, 55, 10000, 10000, test, epsgIn="4326", stepDeg=F, epsgOut="4326")

# geographic coordinates as input, UTM as output, distance between points in meters
test <- "C:/test_geo_to_UTM.csv"
regularGridPoints(5, 45, 10, 55, 10000, 10000, test, epsgIn="4326", stepDeg=F, epsgOut="32632")

# UTM coordinates as input, geographic as output, distance between points in degrees
test <- "C:/test_UTM_to_geo.csv"
regularGridPoints(150000, 5000000, 600000, 6000000, 0.01, 0.01, test, epsgIn="32632", stepDeg=T, epsgOut="4326")
