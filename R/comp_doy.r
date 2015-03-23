### Function to compare day-of-year dates between two datasets. 
### All data vectors must have the same length.
###
### Arguments:
###     x: vector containing the x values
###     y: vector containing the y values
###     addx: vector containing the x values for additional set of points
###     addy: vector containing the y values for additional set of points
###     xycol: the point colour
###     addxycol: the point colour for the additional set of points
###     LU: vector containing the land use class for each point.
###     LUC: single value or (numerical) vector containing the desired land use class by which the data will be filtered.
###     exclude: single value which shall be excluded
###
### Additional plot arguments may be used.

library(rgdal)
source("D:/Uni/Masterarbeit/R_scripts/dummy_scripts/bg_grid_grey.R")

comp_doy <- function(x, y, addx=NULL, addy=NULL, 
                     xycol="forestgreen", addxycol="brown", 
                     LU=NULL, LUC=NULL, exclude=NULL, ...) {
    # exclude desired value:
    if (is.null(exclude) == T){#do nothing
    } else {
        x <- replace(x, which(x == exclude), NA)
        y <- replace(y, which(y == exclude), NA)
    }
    # set up initial plot:
    plot(x, y, bty="n", axes=F, pch=NA, xlim=c(0, 365), ylim=c(0, 365), ...)
    # draw grey box with grid:
    bg_grid_grey()
    # draw 1:1 line:
    lines(x=c(0, 365), y=c(0, 365), col="darkgrey")
    # draw points if no land use class is desired:
    if (is.null(LU) == T) {
        points(x, y, pch=20, col=xycol)
        if (is.null(addx) == T & is.null(addy) == T) {# do nothing
            } else {
            points(addx, addy, pch=20, col=addxycol)
        }
    } else { # filter points for land use class, then draw them:
        sx <- c()
        sy <- c()
        ex <- c()
        ey <- c()
        for (i in 1:length(x)) {
            # check for desired land use class and make sure it is not NA:
            if (LU[i] %in% LUC & is.na(LU[i]) == F) {
                sx <- append(sx, x[i])
                sy <- append(sy, y[i])
                ex <- append(ex, addx[i])
                ey <- append(ey, addy[i])
            } else { # do nothing
                }
        }
        points(sx, sy, pch=20, col=xycol)
        points(ex, ey, pch=20, col=addxycol)
    }
}
