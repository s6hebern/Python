library(rgdal)
library(maptools)

#year = 2012
# read data from shapefile:
data <- readShapePoints("SHAPEFILE.shp")
# get unique class names:
classes <- as.vector(unique(data$COLUMN))
# get counts for each individual class
counts <- as.vector(table(data$COLUMN))

# plot as histogram:
plot(counts, type="h", bty="n", axes=F, xlab="CLASSES", ylab="COUNTS", main="TITLE")
# y-axis:
axis(2)
# add mean, stdv and stdv/2:
abline(h=mean(counts), col="red")
abline(h=mean(counts)+sd(counts), lty=2)
abline(h=mean(counts)+0.5*sd(counts), lty=3)
# add data description (class names) to each class bar (tilted by 45°):
text(1:length(classes), counts+250, labels=sort(classes), srt=45, xpd=T)
# add x-axis with class number at each second tickmark:
axis(1, at=seq(1, length(classes), 2), labels=seq(1, length(classes), 2))
# add another x-axis with tickmarks at each class bar:
axis(1, at=1:length(classes), labels=F)
# add legend:
legend(x=1, y=max(counts), legend=c("mean", "mean + 1/2 stdv.", "mean + 1 stdv."), lty=c(1, 3, 2), 
       col=c("red", "black", "black"), bty="n")
       
       
       test
