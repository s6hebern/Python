requirements <- c("docstring", "data.table")
to_install <- requirements[!(requirements %in% installed.packages()[,"Package"])]
if(length(to_install)) install.packages(to_install)
library(docstring)
library(data.table)

summarizeDT <- function(df, by, modeNumeric="mean", modeOther="first"){
    
    #' Summarize a data.table (or data.frame)
    #' @description Summarize a data.frame-like object (data.frame, data.table, 
    #' etc.) with respect to different data types in its columns
    #' @param df data.frame-like object
    #' @param by Column to base the summary on. Rows with the same value of "by"
    #' will be summarized.
    #' @param modeNumeric Summary mode for numeric values. Default is "mean"
    #' @param modeOther Summary mode for non-numeric values. One of "first" 
    #' (default), "last" or "majority"
    #' @return Summarized data.table
    #' @examples 
    #' my_table <- data.frame(name=c(rep("test", 4)), value=seq(1,4), 
    #' date=c("2018-04-04", "2018-04-04", "2018-04-05", "2018-04-06"))
    #' ## convert string date to date-format
    #' my_table$date <- as.POSIXct(my_table$date, format="%Y-%m-%d")
    #' ## group the data.frame by date with the first  occurence of "date" and 
    #' "name" for the groups
    #' newDt <- summarizeDT(my_table, my_table$date)

    summarize <- function(x, modeNumeric="mean", modeOther="first"){
        if(is.numeric(x)){
            do.call(modeNumeric, list(x))
        } else {
            if(modeOther=="first"){
                head(x, n=1)
            } else if(modeOther=="last"){
                tail(x, n=1)
            } else if(modeOther=="majority"){
                data.table(x)[ , .N, keyby=x][1, 1]
            }
        }
    }
    setDT(df)
    dt <- df[ , lapply(.SD, summarize), by=by]
    return(dt[ ,2:ncol(dt)])
}
