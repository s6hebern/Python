# -*- coding: utf-8 -*-

import os
import ftplib

try:
    import module_progress_bar as pr
except:
    pass

def ftp_download(url, user='', pw='', localPath=os.getcwd(), pattern=None):
    
    """
    Download files from a ftp-server. Can handle one level of subfolders.
    
    Use:
    
    url (string): the complete url of the ftp-server containing the desired 
            files.
    
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

    if url.__contains__('ftp://'):
        url = url.split('//')[1]
    # set up connection:
    ftp = ftplib.FTP(url.split('/')[0])
    ftp.login(user, pw)
    # switch directory on server:
    root = url.lstrip(url.split('/')[0])
    ftp.cwd(root)
    # list all files and/or directories:
    listing = []
    ftp.retrlines('NLST', listing.append)

    # loop through the current directory and get the files:
    for l in listing:
        try:
            pr.progress(l, listing)
        except:
            pass
        
        if l[-4] == '.':
            # check for desired pattern:
            if pattern == None:
                # download files:
                local_filename = os.path.join(localPath, l)
                lf = open(local_filename, 'wb')
                ftp.retrbinary('RETR ' + l, lf.write)
                lf.close()
            else:
                for p in pattern:
                    # download files:
                    if l.__contains__(str(p)):
                        local_filename = os.path.join(localPath, l)
                        lf = open(local_filename, 'wb')
                        ftp.retrbinary('RETR ' + l, lf.write)
                        lf.close()
        else:
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
                        if f.__contains__(str(p)):
                            local_filename = os.path.join(localPath, f)
                            lf = open(local_filename, 'wb')
                            ftp.retrbinary('RETR ' + f, lf.write)
                            lf.close()
        
            ftp.cwd('/..')
            ftp.cwd(root)

    ftp.close()
