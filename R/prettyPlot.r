requirements <- c("docstring")
to_install <- requirements[!(requirements %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install)
library(docstring)

prettyPlot <- function(tickseq, bg.col="lightgrey", grid.col="white",
                       box.col="white", grid.lty=1) {
    
    #' Add background, grid and border to plot
    #' @description This adds a background box and grid lines to an already 
    #' initiated plot.
    #' @param tickseq Sequence of x-values where tickmarks / vertical lines 
    #' shall be placed
    #' @param bg.col Background color
    #' @param grid.col Color of grid lines
    #' @param box.col Color of box around the plot
    #' @param grid.lty Line type of grid lines
    #' @return NULL
    #' @note Beware: the "background" and grid lines are actually drawn in the
    #' foreground, overwriting the initial plot. Set up the plot without 
    #' actually drawing it, then call prettyPlot, then add your data.
    #' @examples 
    #' ## create 10 random numbers
    #' myX <- c(1:10)
    #' myY <- runif(n=10, min=1, max=100)
    #' myTicks <- seq(2, 10, 2)
    #' ## initiate plot
    #' plot(x=myX, y=myY, type="n", axes=F, xlim=c(1, 10), ylim=c(0, max(myY)), 
    #' xlab="X", ylab="Y", main="My Pretty Plot")
    #' ## add axes
    #' axis(1, col="lightgrey")
    #' axis(2, col="lightgrey")
    #' ## call prettyPlot
    #' prettyTsPlot(myTicks)
    #' ## add your data and axes
    #' points(x=myX, y=myY, pch=16)

    rect(par("usr")[1], par("usr")[3], par("usr")[2], par("usr")[4], 
         col=bg.col, border=NA)
    # horizontal lines
    for (h in seq(par("yaxp")[1] - (par("yaxp")[2] - par("yaxp")[1]) / 
                  (par("yaxp")[3] * 2), 
                  par("yaxp")[2] + (par("yaxp")[2] - par("yaxp")[1]) / 
                  (par("yaxp")[3] * 2), 
                  by=(par("yaxp")[2] - par("yaxp")[1]) / (par("yaxp")[3] * 2))) 
    {abline(h=h, col=grid.col, lty=grid.lty)}
    # vertical lines
    ticks <- as.numeric(tickseq)
    for (t in ticks) {abline(v=t, col=grid.col, lty=grid.lty)}
    box(col=box.col)
}requirements <- c("docstring")
to_install <- requirements[!(requirements %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install)
library(docstring)

prettyPlot <- function(tickseq, bg.col="lightgrey", grid.col="white",
                       box.col="white", grid.lty=1) {
    
    #' Add background, grid and border to plot
    #' @description This adds a background box and grid lines to an already 
    #' initiated plot.
    #' @param tickseq Sequence of x-values where tickmarks / vertical lines 
    #' shall be placed
    #' @param bg.col Background color
    #' @param grid.col Color of grid lines
    #' @param box.col Color of box around the plot
    #' @param grid.lty Line type of grid lines
    #' @return NULL
    #' @note Beware: the "background" and grid lines are actually drawn in the
    #' foreground, overwriting the initial plot. Set up the plot without 
    #' actually drawing it, then call prettyPlot, then add your data.
    #' @examples 
    #' ## create 10 random numbers
    #' myX <- c(1:10)
    #' myY <- runif(n=10, min=1, max=100)
    #' myTicks <- seq(2, 10, 2)
    #' ## initiate plot
    #' plot(x=myX, y=myY, type="n", axes=F, xlim=c(1, 10), ylim=c(0, max(myY)), 
    #' xlab="X", ylab="Y", main="My Pretty Plot")
    #' ## add axes
    #' axis(1, col="lightgrey")
    #' axis(2, col="lightgrey")
    #' ## call prettyPlot
    #' prettyTsPlot(myTicks)
    #' ## add your data and axes
    #' points(x=myX, y=myY, pch=16)

    rect(par("usr")[1], par("usr")[3], par("usr")[2], par("usr")[4], 
         col=bg.col, border=NA)
    # horizontal lines
    for (h in seq(par("yaxp")[1] - (par("yaxp")[2] - par("yaxp")[1]) / 
                  (par("yaxp")[3] * 2), 
                  par("yaxp")[2] + (par("yaxp")[2] - par("yaxp")[1]) / 
                  (par("yaxp")[3] * 2), 
                  by=(par("yaxp")[2] - par("yaxp")[1]) / (par("yaxp")[3] * 2))) 
    {abline(h=h, col=grid.col, lty=grid.lty)}
    # vertical lines
    ticks <- as.numeric(tickseq)
    for (t in ticks) {abline(v=t, col=grid.col, lty=grid.lty)}
    box(col=box.col)
}
