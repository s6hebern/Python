# Function to calculate a grid which will be drawn at the major and minor tickmarks of a plot.
# "Major" grid will be white, "minor" grid will be grey.
# Also changes the background colour of the plot to lightgrey.
# Draws grey axis by default. If xy_lines ist set FALSE, axis will not be drawn.
#
# Hints when setting up initial plot:
# - prevent any drawing of your data, do this after calling this function (e.g. with pch=NA)
# - suppress drawing of the box around the plot region and all axis (bty="n", axes=F)

bg_grid_grey <- function(xy_axis=T) {
  # set background colour of the plotting region:
    rect(par("usr")[1], par("usr")[3], par("usr")[2], par("usr")[4], col = "lightgrey", border=NA)
  # draw vertical lines at minor x-tickmarks:
    for (v in seq(par("xaxp")[1], par("xaxp")[2] + (par("xaxp")[2] - par("xaxp")[1]) / 
                    (par("xaxp")[3] * 2), 
                  by=(par("xaxp")[2] - par("xaxp")[1]) / (par("xaxp")[3] * 2))) {
      abline(v=v, col="grey90")
    }
  # draw horizontal lines at minor y-tickmarks:
    for (h in seq(par("yaxp")[1], par("yaxp")[2] + (par("yaxp")[2] - par("yaxp")[1]) / 
                    (par("yaxp")[3] * 2), 
                  by=(par("yaxp")[2] - par("yaxp")[1]) / (par("yaxp")[3] * 2))) {
      abline(h=h, col="grey90")
  # draw grid at major tickmarks (must be after minor grid):
    grid(lty=1, col="white")
    }
  # draw x- and y-axis, if not set FALSE:
  if (xy_axis == T) {
      axis(1, lwd=0, lwd.ticks=1, col="lightgrey")
      axis(2, lwd=0, lwd.ticks=1, col="lightgrey")
  }
}

# Example:
# data <- runif(100, 0, 100) # generate random numbers
# plot(data, pch=NA, bty="n", axes=F) # initial plot (empty)
# bg_grid_grey() # styling
# points(data, pch=20, col="red") # actual data plot
