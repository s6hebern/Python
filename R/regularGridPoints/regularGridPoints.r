regularGridPoints <- function(xmin, ymin, xmax, ymax, stepx, stepy, outfile, 
                              epsgIn="4326", stepDeg=F, epsgOut="4326", show=F) {
  
  #-------------------------------------------------------------------------#
  # check for required package "rgdal", install if necessary
  list.of.packages <- c("rgdal", "ggmap", "data.table")
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
  if(length(new.packages)) install.packages(new.packages)
  require(rgdal)
  require(ggmap)
  require(data.table)
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
  if (epsgIn == "4326" & epsgOut == "4326") {
    #-------------------------------------------------------------------------#
    # if steps are meters
    if (stepDeg == F) {
      # calculate UTM zone
      utm_zone <- as.character((floor((mean(c(xmin_in, xmax_in)) + 180)/6) %% 60) + 1)
      print(paste("Transforming to UTM, Zone ", as.character(utm_zone), "N", sep=""))
      crs_utm <- CRS(paste("+init=epsg:326", utm_zone, sep=""))
      # transform input coordinates to UTM
      XY_utm <- spTransform(XY_in, CRSobj=crs_utm)
      crs_temp <- crs_utm
      # extract temporary corner coordinates (now in UTM)
      xmin_utm <- as.numeric(XY_utm[1]$X)
      ymin_utm <- as.numeric(XY_utm[1]$Y)
      xmax_utm <- as.numeric(XY_utm[2]$X)
      ymax_utm <- as.numeric(XY_utm[2]$Y)
      # calculate all possible distinct x and y values (in UTM)
      xvals <- seq(xmin_utm, xmax_utm, by=stepx)
      yvals <- seq(ymin_utm, ymax_utm, by=stepy)
    } else { # steps are degrees
      # calculate all possible distinct x and y values (in degrees)
      xvals <- seq(xmin_in, xmax_in, by=stepx)
      yvals <- seq(ymin_in, ymax_in, by=stepy)
      crs_temp <- crs_in
    }
    #-------------------------------------------------------------------------#
  } else if (epsgIn == "4326" & epsgOut != "4326") { # input CRS is geographic, output CRS it other
    #-------------------------------------------------------------------------#
    # if steps are in meters
    if (stepDeg == F) {
      # calculate all possible distinct x and y values (in output CRS)
      xvals <- seq(xmin_out, xmax_out, by=stepx)
      yvals <- seq(ymin_out, ymax_out, by=stepy)
      crs_temp <- crs_out
    } else { # steps are in degrees
      # calculate all possible distinct x and y values (in degrees)
      xvals <- seq(xmin_in, xmax_in, by=stepx)
      yvals <- seq(ymin_in, ymax_in, by=stepy)
      crs_temp <- crs_in
    }
    #-------------------------------------------------------------------------#
  } else if (epsgIn != "4326" & epsgOut != "4326") { # both CRS are metric
    #-------------------------------------------------------------------------#
    # if steps are in meters
    if (stepDeg == F) {
      # calculate all possible distinct x and y values (in meters)
      xvals <- seq(xmin_out, xmax_out, by=stepx)
      yvals <- seq(ymin_out, ymax_out, by=stepy)
      crs_temp <- crs_out
    } else { # steps in degrees --> throw error message
      stop("If neither your input nor your output coordinate systems are 
           geographic (EPSG: 4326), you can't use stepDeg=TRUE! Please set 
           it to FALSE and provide stepx and stepy in meters!")
    }
    #-------------------------------------------------------------------------#
    } else if (epsgIn != "4326" & epsgOut == "4326") { # input CRS is metric, output CRS it geographic
      #-------------------------------------------------------------------------#
      # if steps are in meters
      if (stepDeg == F) {
        # calculate all possbile distinct x and y values (in neters)
        xvals <- seq(xmin_in, xmax_in, by=stepx)
        yvals <- seq(ymin_in, ymax_in, by=stepy)
        crs_temp <- crs_in
      } else { # steps are in degrees
        # calculate all possible distinct x and y values (in degrees)
        xvals <- seq(xmin_out, xmax_out, by=stepx)
        yvals <- seq(ymin_out, ymax_out, by=stepy)
        crs_temp <- crs_out
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
  flatgrid <- data.table(xlist, ylist)
  # if another transform is needed to match output CRS
  epsg_temp <- substr(CRSargs(crs_temp), 
                      as.numeric(regexpr("epsg:", CRSargs(crs_temp)))+5, 
                      as.numeric(regexpr("+proj", CRSargs(crs_temp)))-3)
  if (epsg_temp != epsgOut) {
    # make SpatialPointsDataFrame and provide coordinate columns
    coordinates(flatgrid) <- c("xlist", "ylist")
    # assign current CRS
    proj4string(flatgrid) <- crs_temp
    flatgrid <- spTransform(flatgrid, crs_out)
  }
  # add ID column
  flatgrid <- as.data.table(flatgrid)
  # calculate total number of points for ID
  coordcount <- length(xvals) * length(yvals)
  print(paste("Total number of points created:", coordcount))
  # fill ID column
  flatgrid <- cbind(seq(1, coordcount), flatgrid)
  # set new column names
  colnames(flatgrid) <- c("ID", "X", "Y")
  # export to csv
  fwrite(flatgrid, file=outfile, sep=",")
  print(paste("Output written to:", outfile))
  
  #############################################################################
  # plot map if desired
  if (show == T) {
    print("Drawing map...")
    print("This may take a while, even after the process itself is finished, so stay patient.")
    mapData <- flatgrid
    # if coordinates are not geographic
    if (epsgOut != "4326") {
      coordinates(mapData) <- c("X", "Y")
      proj4string(mapData) <- crs_out
      mapData <- spTransform(mapData, CRS("+init=epsg:4326"))
      mapData <- as.data.table(mapData)
    }
    # get initial map
    map <- get_map(location=make_bbox(lon=X, lat=Y, data=mapData), zoom=calc_zoom(lon=X, lat=Y, data=mapData) - 2,
                   maptype="terrain", source="google", color="bw")
    # plot webmap and add points
    ggmap(map, maprange=F) +
      geom_point(aes(x=X, y=Y), data=mapData, color="red", size=2)
  }
}
