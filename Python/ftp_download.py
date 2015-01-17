# -*- coding: utf-8 -*-

import os
import ftplib

def ftp_download(server, serverPath, user='', pw='', localPath=os.getcwd(), pattern=None):
    
    """
    Download files from a ftp-server.
    
    Use:
    
    server (string): the base adress of the ftp-server (without any links, just
            the basic adress of the main page (top level domain)).
    
    serverPath (string): the path within the servers file structure, which is 
            the rest of the whole url after the top level domain ('.com', 
            '.gov', etc.).
    
    user (string): 'Username' for server login.
    
    pw (string): 'Password' for server login.
    
    localPath (string): the local directory, to which the files shall be 
            downloaded. Defaults to the current working directory.
    
    pattern (list): a lit of string containing the pattern of characters to look 
            for in the file names as a list. May be useful, if there are many 
            files from which only a selection shall be taken.
            Examples:    
                pattern='.txt' (if all txt-files are desired)
                pattern='_mean' (if all desired files include that 
                                        particular string in the name)
    """

    if server.__contains__('ftp://'):
        server = server.strip('ftp://')
    # set up connection:
    ftp = ftplib.FTP(server)
    ftp.login(user, pw)
    # switch directory on server:
    root = serverPath
    ftp.cwd(root)
    # list all files and / or directories:
    listing = []
    ftp.retrlines('NLST', listing.append)
    # loop through the current directory and get the files:
    for l in listing:
        # get file names:
        files = []
        ftp.cwd(l)
        ftp.retrlines('NLST', files.append)
        # check for desired pattern:
        if pattern == None:
            for f in files:
                # download files:
                local_filename = os.path.join(localPath, f)
                lf = open(local_filename, 'wb')
                ftp.retrbinary('RETR ' + f, lf.write)
                lf.close()
        else:
            for p in pattern:
                for f in files:
                    # download files:
                    if f.__contains__(p):
                        local_filename = os.path.join(localPath, f)
                        lf = open(local_filename, 'wb')
                        ftp.retrbinary('RETR ' + f, lf.write)
                        lf.close()
    
        ftp.cwd('/..')
        ftp.cwd(root)


##------------------------------------------------------------------------------
## Example:
#
#pat = ['_' + str(i) for i in xrange(2001, 2015)]        
#ftp_download('ftp-cdc.dwd.de', 'pub/CDC/grids_germany/monthly/air_temperature_mean', \
#    r'D:\Uni\Masterarbeit\climate\airtemp_monthly', pattern=pat)
