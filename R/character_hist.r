# Function to calculate a histogram of character values, which in most cases represent class names.
#
# Usage:
# - data: a vector-like object containing the character classes to be analyzed
# - stat_lines: if set TRUE, lines for mean and standard deviation and legend will be drawn
# - data_desc: will write the respective class name at the top of each histogram bar

char_hist <- function(data, stat_lines=F, data_desc=T, ...) {
  # get unique class names:
  classes <- as.vector(unique(data))
  # get counts for each individual class
  counts <- as.vector(table(data))
  # plot as histogram:
  plot(counts, type="h", bty="n", axes=F, ...)
  # y-axis:
  axis(2)
  # add mean, stdv, stdv/2 and legend if stat_lines == T:
  if (stat_lines == T) {
      abline(h=mean(counts), col="red")
      abline(h=mean(counts) + sd(counts), lty=2)
      abline(h=mean(counts) - sd(counts), lty=2)
      abline(h=mean(counts) + 0.5*sd(counts), lty=3)
      abline(h=mean(counts) - 0.5*sd(counts), lty=3)
      legend(x=1, y=max(counts), legend=c("mean", "mean +|- 1/2 stdv.", "mean +|- 1 stdv."), 
             lty=c(1, 3, 2), col=c("red", "black", "black"), bty="n")
  }
  # add data description (class names) to each class bar (tilted by 45°) if data_desc == T:
  if (data_desc == T) {
      text(1:length(classes), counts+max(counts)/100*5, labels=sort(classes), srt=45, xpd=T)
  }
  # add x-axis with class number at each second tickmark:
  axis(1, at=seq(1, length(classes), 2), labels=seq(1, length(classes), 2))
  # add another x-axis with tickmarks at each class bar:
  axis(1, at=1:length(classes), labels=F)
}

# Example:
# data <- c(rep("January", 5), rep("Febuary", 3), rep("March", 15), rep("April", 11), 
#           rep("May", 3), rep("June", 8), rep("July", 5), rep("August", 2), 
#           rep("September", 6),rep("October", 7),rep("November", 1), rep("December", 10))
# char_hist(data, main="Counting Months", xlab="Month", ylab="Counts")
