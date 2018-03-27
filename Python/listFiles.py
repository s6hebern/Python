import os
import fnmatch

# function to recursively loop a directory
def listFiles(path, pattern=None, full=True, recurse=True):
    """
    Recurse into the given directory and searches for all files containing the given wildcard pattern.

    :param str path: Path to the directory that shall be searched
    :param str pattern: String pattern to be mandatory within the filename
    :param bool full: Full path and file name (True; default) or file name only (False)
    :param bool recurse: Recurse into subfolders (True; default) or not (False)
    :return: List of files
    :rtype: list

    :example: shapes = listFiles(export_path, pattern='*.shp', full=True, recurse=True)
    """

    filelist = []
    if recurse is True:
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if fnmatch.fnmatchcase(filename, pattern):
                    if full is True:
                        filelist.append(os.path.join(root, filename))
                    else:
                        filelist.append(filename)
    else:
        for f in os.listdir(path):
            if fnmatch.fnmatchcase(f, pattern):
                if full is True:
                    filename = os.path.join(path, f)
                else:
                    filename = f
                filelist.append(filename)
    return filelist
