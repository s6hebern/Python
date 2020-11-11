import os
import fnmatch


def list_files(path, pattern=None, full=True, recurse=True, ignore=None):
    # type: (str, str, bool, bool, str) -> list
    """
    Recurse into the given directory and search for all files containing the given wildcard pattern.

    Example: shapes = listFiles(export_path, pattern='*.shp', full=True, recurse=True)

    :param path: Path to the directory that shall be searched
    :param pattern: String pattern to be mandatory within the filename
    :param full: Full path and file name (True; default) or file name only (False)
    :param recurse: Recurse into subfolders (True; default) or not (False)
    :param ignore: If the file name or the full path (depending on parameter "full") contains this
            string, it will be ignored.
    :return: List of files

    """
    if not os.path.exists(path):
        raise SystemError('Path {p} does not exist!'.format(p=path))
    filelist = []
    if recurse is True:
        for root, __subdirs, files in os.walk(path):
            for filename in files:
                if fnmatch.fnmatchcase(filename, pattern):
                    if full is True:
                        if ignore:
                            if ignore not in os.path.join(root, filename):
                                filelist.append(os.path.join(root, filename))
                            else:
                                continue
                        else:
                            filelist.append(os.path.join(root, filename))
                    else:
                        if ignore:
                            if ignore not in filename:
                                filelist.append(filename)
                            else:
                                continue
                        else:
                            filelist.append(filename)
    else:
        for f in os.listdir(path):
            if fnmatch.fnmatchcase(f, pattern):
                if full is True:
                    if ignore:
                        if ignore not in os.path.join(path, f):
                            filelist.append(os.path.join(path, f))
                        else:
                            continue
                    else:
                        filelist.append(os.path.join(path, f))
                else:
                    if ignore:
                        if ignore not in f:
                            filelist.append(f)
                        else:
                            continue
                    else:
                        filelist.append(f)
    return filelist


def list_dirs(path, pattern=None, full=True, recurse=True, ignore=None):
    # type: (str, str, bool, bool, str) -> list
    """
    Recurse into the given directory and search for all subfolders containing the given wildcard pattern.

    Example: dirs = listDirs(r'd:/working/testing', pattern='*test*', full=True, recurse=True)

    :param path: Path to the main directory that shall be searched
    :param pattern: String pattern to be mandatory within the filename
    :param full: Full path and folder name (True; default) or folder name only (False)
    :param recurse: Recurse into subfolders (True; default) or not (False)
    :param ignore: If the folder name or the full path (depending on parameter "full") contains
            this string, it will be ignored.
    :return: List of directories
    """
    if not os.path.exists(path):
        raise SystemError('Path {p} does not exist!'.format(p=path))
    dirlist = []
    if recurse is True:
        for root, subdirs, __files in os.walk(path):
            for sub in subdirs:
                if fnmatch.fnmatchcase(sub, pattern) and os.path.isdir(os.path.join(root, sub)):
                    if full is True:
                        if ignore:
                            if ignore not in os.path.join(root, sub):
                                dirlist.append(os.path.join(root, sub))
                            else:
                                continue
                        else:
                            dirlist.append(os.path.join(root, sub))
                    else:
                        if ignore:
                            if ignore not in sub:
                                dirlist.append(sub)
                            else:
                                continue
                        else:
                            dirlist.append(sub)
    else:
        for f in os.listdir(path):
            if fnmatch.fnmatchcase(f, pattern) and os.path.isdir(os.path.join(path, f)):
                if full is True:
                    if ignore:
                        if ignore not in os.path.join(path, f):
                            dirlist.append(os.path.join(path, f))
                        else:
                            continue
                    else:
                        dirlist.append(os.path.join(path, f))
                else:
                    if ignore:
                        if ignore not in f:
                            dirlist.append(f)
                        else:
                            continue
                    else:
                        dirlist.append(f)
    return dirlist
