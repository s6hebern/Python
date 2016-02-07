#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
date: Thu Feb  4 15:57:32 2016
user: hendrik
"""

try:
    import geocoder
    gc = True
    req = False
except:
    try:
        import requests
        req = True
        gc = False
    except:
        raise ValueError('None of the two libraries "geocoder" and \
                            "requests" is installed! Please install at \
                            least one of them and try again!')

import csv


class geoCoding():
    
    """
    Geocode a tabular file, e.g. a csv-file, containing postal adresses. These 
        adresses will be converted into geographical coordinates. 
        The input file has to contain all relevant postal information, most 
        importantly street, number, zip-code and city, in separate columns.
    
    Thankfully taking advantage of this great module: 
            
            https://pypi.python.org/pypi/geocoder/
    
    ATTENTION: make sure that the header of your input file contains only 
            single-lined cells! A linebreak within a cell will cause the 
            program to do strange things or even crash!
            Same thing with the delimiter used in the input file: it should 
            ONLY be used as the delimiter and not within the data!
        
        Initial arguments:
        
        infile (string): the input file containing the adresses (full path and 
                file extension)
        
        sep (string): the delimiter used within the input file to discriminate
                columns
        
        header (boolean): if "True" (default), the first row of the input file 
                is considered to be the header, containing the column names. If 
                there is no header, set it to "False"
        
        cols (list): a list of integers, containing the columns in which the 
                single parts of the adress appear. If "None" (default), it is
                considered that each row only contains the adress and nothing 
                else. Column-counting starts at 1.
    """
    
    def __init__ (self, infile, sep, header=True, cols=None):
        # set initial variables
        self.infile = infile
        self.sep = sep
        self.header = header
        self.cols = cols

    # read input file
    def readFile(self):
        with open(self.infile, 'r') as f:
            # read data and remove linebreaks
            lines = []
            for l in f.readlines():
                row = l.strip('\n')
                row = row.split(self.sep)
                lines.append(row)
        f.close()
        # return data
        return lines
        
    # extract adresses from csv
    def getAdresses(self, consoleOut=False):
        
        """
        Get the adresses from the input file. 
        
        Usage:
        
        consoleOut (boolean): if "True", the adresses will be printed to the 
                current Python console. "False" (default) suppresses printing.
        """
        
        # open file
        lines = self.readFile()
        # if there is a header, remove it
        if self.header == True:
            lines = lines[1:len(lines)]
        # get adress from relevant columns, if other columns are present
        adresses = []
        for l in xrange(len(lines)):
            if self.cols != None:
            # split linestring to single strings
                adress = [lines[l][c-1] for c in self.cols]
                # create query
                adresses.append(','.join(adress))
            else:
                adresses.append(lines[l])
        # print adresses to console
        if consoleOut == True:
            print adresses
        # return list of all adresses
        return adresses

    # convert adresses to coordinates using one of the two available modules
    def adress2coords(self, consoleOut=False, addID=False):
        
        """
        Convert addresses to geographical coordinates using one of the two 
                libraries "geocoder" or "requests". If both are installed, 
                "geocoder" is used.
        
        Usage:
        
        consoleOut (boolean): if "True", the coordinates will be printed to the 
                current Python console. "False" (default) suppresses printing.
        
        addID (boolean): if "True", an ID-column will be added as the first 
                element of the output. Defaults to "False".
        """
        
        print 'Converting adresses to coordinates...'
        # use "geocoder"-library
        if gc == True:
            # get adresses
            adresses = self.getAdresses()
            # use geocoder-module
            queries = [geocoder.google(a) for a in adresses]
            coords = [tuple(q.latlng) for q in queries]
            # create unique id, if desired
            if addID == True:
                coords = [(c+1,) + coords[c] for c in xrange(len(coords))]
        # use "request"-library
        elif req == True:
            url = 'https://maps.googleapis.com/maps/api/geocode/json'
            # get adresses
            adresses = self.getAdresses()
            # use requests-module
            locations = []
            for a in xrange(len(adresses)):
                params = {'sensor': 'false', 'address': adresses[a]}
                r = requests.get(url, params=params)
                results = r.json()['results']
                locations.append(results[0]['geometry']['location'])
            coords = [(l['lat'], l['lng']) for l in locations]
            # create unique id, if desired
            if addID == True:
                coords = [(c+1,) + coords[c] for c in xrange(len(coords))]
        # if none of the two modules is installed, print Error-message
        else:
            raise ValueError('None of the two libraries "geocoder" and \
                            "requests" is installed! Please install at \
                            least one of them and try again!')
        # print coordinates to console, if desired
        if consoleOut == True:        
            print coords
        # return coordinates
        print 'Done!'
        return coords

    # write output file, coordinates only
    def coords2csv(self, outfile, addID=False):
        
        """
        Write (only) the coordinates to a csv-file.
        
        Usage:
        
        outfile (string): the output file, to which the coordinates shall be 
                written (full path and file extension).
        addID (boolean): if "True", an ID-column will be added as the first 
                element of the output. Defaults to "False".
        """
        
        # open file for writing
        with open(outfile, 'wb') as f:
            writer = csv.writer(f, delimiter=self.sep)
            # create headline
            if addID == False:
                header = ['Lat', 'Lng']
                # get coordinates
                coords = self.adress2coords(addID=False)
            else:
                header = ['ID', 'Lat', 'Lng']
                # get coordinates
                coords = self.adress2coords(addID=True)
            # write data
            writer.writerow(header)            
            writer.writerows(coords)
        # close file
        f.close()
        
    # add coordinates (and an ID, if desired) to input data
    def addCoords(self, headerExt=['Lat', 'Lng'], addID=False):
        """
        Append geographic coordinates to each row of the input file.
        
        Usage:
        
        headerExt (list): a list of strings, giving the column names for the 
                coordinate-columns. Defaults to "['Lat', 'Lng']". Use "False" 
                if there is no header.
        
        addID (boolean): if "True", an ID-column will be added as the first 
                element of the output. Defaults to "False".
        """
        
        # open file
        lines = self.readFile()
        # extend header, if there is one
        if headerExt != False:
            header = lines[0]
            # add ID, if desired:
            if addID == True:
                header.insert(0, 'ID')
            # remove header from lines
            data = lines[1:len(lines)]
            for h in headerExt:
                header.append(h)
        else:
            data = lines
        # append coordinates to each line (with addID=False, ID is added before, if desired)
        coords = self.adress2coords(addID=False)
        # append coordinates to each row
        for d in xrange(len(data)):
            # check for empty coordinates (request has failed)
            if len(coords[d])==2:
                data[d].append(str(coords[d][0]))
                data[d].append(str(coords[d][1]))
            else:
                # if the request has failed, use impossible values as coordinates
                data[d].append(str(999))
                data[d].append(str(999))
            # add ID, if desired
            if addID==True:
                data[d].insert(0, d+1)
        # insert header
        if headerExt != False:
            data.insert(0, header)
        # return full data
        return data
        
        
    def writecsv(self, headerExt=['Lat', 'Lng'], addID=False, update=True, outfile=None):
        
        """
        Write a new or update the input csv-file by appending the coordinates 
                to each row of the input file.
        
        Usage:
        
        headerExt (list): a list of strings, giving the column names for the 
                coordinate-columns. Defaults to "['Lat', 'Lng']". Use "False" 
                if there is no header.
        
        addID (boolean): if "True", an ID-column will be added as the first 
                element of the output. Defaults to "False".
                
        update (boolean): if "True" (default), the input file will be updated 
                by appending columns for the coordinates. If "False", a new 
                csv-file will be written, containing everything from the input 
                file plus the coordinates (and an ID if desired). In that case, 
                an output file must be given.
        
        outfile (String): the output csv-file, if "update" is "False" (full 
                path and file extension).
        """
        
        # get data
        lines = self.addCoords(headerExt, addID)
        # check for header
        if headerExt != False:
            header = lines[0]
            data = lines[1:len(lines)]
        else:
            data = lines
        # write output file, either update existing or create a new one
        if update == True:
            # open file again, this time in truncating read-write mode   
            with open(self.infile, 'w+') as f:
                writer = csv.writer(f, delimiter=self.sep)
                # write new header
                if headerExt != False:
                    writer.writerow(header)
                # write data
                writer.writerows(data)
                f.close()
        else:
            if outfile != None:
                with open(outfile, 'w') as f:
                    writer = csv.writer(f, delimiter=self.sep)
                    # write new header
                    if headerExt != False:
                        writer.writerow(header)
                    # write lines
                    writer.writerows(data)
                    f.close()
            else:
                raise ValueError('Please specify an output file first!')
    
    # check if string can be represented as a number
    def isNumber(self, string):
        
        """
        Test if a string can be converted to a number
        """
        
        try:
            float(string)
            return True
        except:
            return False
        
    # write shapefile
    def adress2shp(self, shapefile, headerExt=['Lat', 'Lng'], addID=False):
        
        """
        Convert adresses to geographical coordinates (WGS84) and write a 
                shapefile, containing the full data from the input file and the
                coordinates. Column names from the file's header will be 
                truncated if they exceed 10 characters.
        
        Usage:
        
        shapefile (string): the output shapefile (full path and file extension)
        
        headerExt (list): a list of strings, giving the column names for the 
                coordinate-columns. Defaults to "['Lat', 'Lng']". Use "False" 
                if there is no header.
        
        addID (boolean): if "True", an ID-column will be added as the first 
                element of the output. Defaults to "False".
        """
        
        # import necessary modules
        import os, re
        from osgeo import ogr, osr

        # get data:
        lines = self.addCoords(headerExt, addID)
        # check for header
        if self.header == True:
            header = lines[0]
            data = lines[1:len(lines)]
        else:
            data = lines
        print "Creating output..."
        # create fields types using first row of data
        row = data[0]
        fTypes = []
        for r in row:
            if self.isNumber(r) == False:
                # assign field type "string"
                fTypes.append(ogr.OFTString)
            else:
                # check for "int" or "float"
                try:
                    int(r)
                    # assign field type "integer"
                    fTypes.append(ogr.OFTInteger)
                except:
                    # assign field type "float"
                    fTypes.append(ogr.OFTReal)
        # create field widths
        fWidths = [0] * len(data[0])
        # get maximum widhts for each column
        for row in data:
            lens = []
            # loop through each element in each row
            for r in row:
                # get lenghts of each element
                lens.append(len(str(r)))
            for l in xrange(len(lens)):
                # check if lenghts are greater than existing ones
                if fWidths[l] < lens[l]:
                    fWidths[l] = lens[l]
        # for floating numbers, reserve 6 digits more for precision
        for w in xrange(len(fWidths)):
            if fTypes[w] == 2:
                fWidths[w] = fWidths[w] + 6
        # create field names
        if self.header == True:
            fNames = []
            # truncate field names to a maximum of 10 characters
            for h in xrange(len(header)):
                if len(header[h]) > 10:
                    fNames.append(header[h][0:10])
                else:
                    fNames.append(header[h])
        else:
            # create dummy field names
            fNames = ["Field_" + str(f) for f in xrange(len(data[0]))]
        # delete characters which are not in the following list:
        fNames = [re.sub(r'[^a-zA-Z0-9_-]', r'', str(n)) for n in fNames]
        # create shapefile
        driver = ogr.GetDriverByName('ESRI Shapefile')
        # set spatial reference system to geographic
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        # check if shapefile already exists and delete it
        if os.path.exists(shapefile):
            driver.DeleteDataSource(shapefile)
        shp = driver.CreateDataSource(shapefile)
        # create point layer
        lyr = shp.CreateLayer('point', srs, geom_type=ogr.wkbPoint)
        # create attribute fields in output shapefile:
        for f in xrange(len(fNames)):
            field =  ogr.FieldDefn(fNames[f], fTypes[f])
            field.SetWidth(fWidths[f])
            # set precision for floats
            if fTypes[f] == ogr.OFTReal:
                field.SetPrecision(6)
            # create fields
            lyr.CreateField(field)
            field = None
        # create features
        featDefn = lyr.GetLayerDefn()
        # draw points and set fields
        for row in xrange(len(data)):
            # create initial feature
            feat = ogr.Feature(featDefn)
            # create initial point
            point = ogr.Geometry(ogr.wkbPoint)
            # add coordiantes (are always the last two elements of each row)
            point.AddPoint(float(data[row][-1]), float(data[row][-2]))
            feat.SetGeometry(point)
            # set field values
            for f in xrange(len(fNames)):
                feat.SetField(fNames[f], data[row][f])
            # set point to feature
            lyr.CreateFeature(feat)
            # clean up
            feat = None
        # clean up
        lyr = None
        print "Done!"
