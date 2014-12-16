# Function to calculate a grid which will be drawn at the major and minor tickmarks of a plot.
# "Major" grid will be white, "minor" grid will be grey.
# Also changes the background colour of the plot to lightgrey.

bg_grid_grey <- function() {
    rect(par("usr")[1], par("usr")[3], par("usr")[2], par("usr")[4], col = "lightgrey", border=NA)
    for (v in seq(par("xaxp")[1], par("xaxp")[2] + par("xaxp")[2]/(par("xaxp")[3]*2), 
                  par("xaxp")[2]/(par("xaxp")[3]*2))) {
      abline(v=v, col="grey90")
    }
    
    for (h in seq(par("yaxp")[1], par("yaxp")[2] + par("yaxp")[2]/(par("yaxp")[3]*2), 
                  par("yaxp")[2]/(par("yaxp")[3]*2))) {
      abline(h=h, col="grey90")
    }
    grid(lty=1, col="white")
}
