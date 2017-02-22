regularGridPoints <- function(xmin, ymin, xmax, ymax, stepx, stepy, out, epsgIn="4326", stepDeg=F, epsgOut="4326") {
  #-------------------------------------------------------------------------#
  # check for required package "rgdal", install if necessary
  list.of.packages <- c("rgdal")
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
  if(length(new.packages)) install.packages(new.packages)
  library(rgdal)
  #-------------------------------------------------------------------------#
  
  xmin_in <- xmin
  ymin_in <- ymin
  xmax_in <- xmax
  ymax_in <- ymax
  # create SpatialPointsDataFrame from input coordinates
  X <- c(xmin_in, xmax_in)
  Y <- c(ymin_in, ymax_in)
  XY_in <- data.frame(X, Y)
  coordinates(XY_in) <- c("X", "Y")
  # set up CRS references
  crs_in <- CRS(paste("+init=epsg:", epsgIn, sep=""))
  print(paste("EPSG of input CRS:", epsgIn))
  crs_out <- CRS(paste("+init=epsg:", epsgOut, sep=""))
  print(paste("EPSG of output CRS:", epsgOut))
  # assign input CRS
  proj4string(XY_in) <- crs_in
  # transform to output CRS (if necessary)
  if (epsgOut != epsgIn) {
    XY_out <- spTransform(XY_in, CRSobj=crs_out)
  } else {
    XY_out <- XY_in
  }
  # get new corner coordinates
  xmin_out <- as.numeric(XY_out[1]$X)
  ymin_out <- as.numeric(XY_out[1]$Y)
  xmax_out <- as.numeric(XY_out[2]$X)
  ymax_out <- as.numeric(XY_out[2]$Y)

  #############################################################################
  # create list of necessary x- and y-values
  #############################################################################
    
  # if input and output CRS are in degrees
  if(epsgIn == "4326" & epsgOut == "4326") {
    #-------------------------------------------------------------------------#
    # if steps are degrees
    if (stepDeg == T) {
      # calculate all possible distinct x and y values (in degrees)
      xvals <- seq(xmin_out, xmax_out, by=stepx)
      yvals <- seq(ymin_out, ymax_out, by=stepy)
    } else { # steps are in meters
      # calculate UTM zone
      utm_zone <- as.character((floor((mean(c(xmin_in, xmax_in)) + 180)/6) %% 60) + 1)
      crs_utm <- CRS(paste("+init=epsg:326", utm_zone, sep=""))
      # transform input coordinates to UTM
      XY_utm <- spTransform(XY_in, CRSobj=crs_utm)
      recent_crs <- crs_utm
      # extract temporary corner coordinates (now in UTM)
      xmin_utm <- as.numeric(XY_utm[1]$X)
      ymin_utm <- as.numeric(XY_utm[1]$Y)
      xmax_utm <- as.numeric(XY_utm[2]$X)
      ymax_utm <- as.numeric(XY_utm[2]$Y)
      # calculate the number of all possible distinct x- and y-values (in UTM)
      xcount <- length(seq(xmin_utm, xmax_utm, by=stepx))
      ycount <- length(seq(ymin_utm, ymax_utm, by=stepy))
      # calculate all possible distinct x and y values (in degrees)
      xvals <- seq(xmin_out, xmax_out, length.out=xcount)
      yvals <- seq(ymin_out, ymax_out, length.out=ycount)
    }
    #-------------------------------------------------------------------------#
  } else if (epsgIn == "4326" & epsgOut != "4326") { # input CRS is geographic, output CRS it other
    #-------------------------------------------------------------------------#
    # if steps are in degrees
    if (stepDeg == T) {
      # calculate the number of all possible distinct x- and y-values (in degrees)
      xcount <- length(seq(xmin_in, xmax_in, by=stepx))
      ycount <- length(seq(ymin_in, ymax_in, by=stepy))
      # calculate all possible distinct x and y values (in desired CRS)
      xvals <- seq(xmin_out, xmax_out, length.out=xcount)
      yvals <- seq(ymin_out, ymax_out, length.out=ycount)
    } else { #steps are in meters
      # calculate all possible distinct x and y values (in meters)
      xvals <- seq(xmin_out, xmax_out, by=stepx)
      yvals <- seq(ymin_out, ymax_out, by=stepy)
    }
    #-------------------------------------------------------------------------#
  } else if (epsgIn != "4326" & epsgOut != "4326") {
    #-------------------------------------------------------------------------#
    # if steps are in degrees, throw error message
    if (stepDeg == T) {
      stop("If neither your input nor your output coordinate systems are geographic (EPSG: 4326), you can't use stepDeg=TRUE! Please set it to FALSE and provide stepx and stepy in meters!")
    } else {
      # calculate all possible distinct x and y values (in meters)
      xvals <- seq(xmin_out, xmax_out, by=stepx)
      yvals <- seq(ymin_out, ymax_out, by=stepy)
    }
    #-------------------------------------------------------------------------#
  } else if (epsgIn != "4326" & epsgOut == "4326") {
    #-------------------------------------------------------------------------#
    # if steps are in degrees
    if (stepDeg == T) {
      # calculate the number of all possible distinct x- and y-values (in degrees)
      xcount <- length(seq(xmin_out, xmax_out, by=stepx))
      ycount <- length(seq(ymin_out, ymax_out, by=stepy))
      # calculate all possible distinct x and y values (in desired CRS)
      xvals <- seq(xmin_out, xmax_out, length.out=xcount)
      yvals <- seq(ymin_out, ymax_out, length.out=ycount)
    } else {
      # calculate the number of all possible distinct x- and y-values (in meters)
      xcount <- length(seq(xmin_in, xmax_in, by=stepx))
      ycount <- length(seq(ymin_in, ymax_in, by=stepy))
      # calculate all possible distinct x and y values (in desired CRS)
      xvals <- seq(xmin_out, xmax_out, length.out=xcount)
      yvals <- seq(ymin_out, ymax_out, length.out=ycount)
    }
    #-------------------------------------------------------------------------#
  }
  
  #############################################################################
  # create output
  #############################################################################
  
  # all necessary x values
  xlist <- rep(xvals, times=length(yvals))
  # all necessary y values
  ylist <- c()
  for (y in yvals) {
    ylist <- c(ylist, rep(y, times=length(xvals)))
  }
  # combine both lists to one table
  flatgrid <- data.frame(xlist, ylist)
  # make SpatialPointsDataFrame and provide coordinate columns
  coordinates(flatgrid) <- c("xlist", "ylist")
  # assign output CRS
  proj4string(flatgrid) <- crs_out
  # add ID column
  flatgrid <- as.data.frame(flatgrid)
  coordcount <- length(xvals) * length(yvals)
  print(paste("Total number of points created:", coordcount))
  flatgrid <- cbind(seq(1, coordcount), flatgrid)
  colnames(flatgrid) <- c("ID", "X", "Y")
  # export to csv
  write.table(flatgrid, file=out, sep=",", row.names=F)
  print(paste("Output written to:", out))
}
