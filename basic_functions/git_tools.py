import os
import subprocess as sub


def setup(path, user_name, user_mail):
    # type (str, str, str) -> None
    """
    Provide git with your username and registered email address

    :param path: Parent directory of the git repository
    :param user_name: Git user name
    :param user_mail: Registered git email address
    :return: --
    """
    os.chdir(path)
    cmd = ['git', 'config', 'user.name', user_name]
    sub.call(cmd)
    cmd = ['git', 'config', 'user.mail', user_mail]
    sub.call(cmd)
    return


def clone(path, repository, only_subdirs=False):
    # type: (str, str, bool) -> None
    """
    Clone an existing repository to your local machine

    :param path: Parent directory of the git repository
    :param repository: URL to repository
    :param only_subdirs: Only clone the subdirectories without the repository name as the parent folder
    :return: --
    """
    os.chdir(path)
    cmd = ['git', 'clone', repository]
    if only_subdirs is True:
        cmd.append('.')
    sub.call(cmd)
    return


def status(path):
    # type: (str) -> None
    """
    Get the current status of your local gut project

    :param path: Parent directory of the git repository
    :return: --
    """
    os.chdir(path)
    cmd = ['git', 'status']
    sub.call(cmd)
    return


def pull(path):
    # type: (str) -> None
    """
    Update from repository

    :param path: Parent directory of the git repository
    :return: --
    """
    os.chdir(path)
    cmd = ['git', 'pull']
    sub.call(cmd)
    return


def commit(path, message, add=True, direct_push=False):
    # type: (str, str, bool, bool) -> None
    """
    Commit (and potentially push) latest changes

    :param path: Parent directory of the git repository
    :param message: Commit message
    :param add: Use "git add" to add non-versioned files
    :param direct_push: Direct push
    :return: --
    """
    os.chdir(path)
    if add is True:
        cmd = ['git', 'add']
        sub.call(cmd)
    cmd = ['git', 'commit', '-m', message]
    sub.call(cmd)
    if direct_push is True:
        cmd = ['git', 'push']
        sub.call(cmd)
    return


def push(path):
    # type: (str) -> None
    """
    Push all staged commits

    :param path: Parent directory of the git repository
    :return: --
    """
    os.chdir(path)
    cmd = ['git', 'push']
    sub.call(cmd)
    return


def create_keep_file(path, recurse=True):
    # type: (str, bool) -> None
    """
    Create .keep files within a folder that shall be kept within git even if it is empty

    :param path: Parent directory or directory to be kept
    :param recurse: Recurse into subfolders
    :return: --
    """
    if recurse is True:
        for root, subdirs, _files in os.walk(path):
            for subd in subdirs:
                subpath = os.path.join(root, subd)
                if os.path.isdir(subpath) and not os.listdir(subpath) and '.git' not in subpath:
                    with open(os.path.join(root, subd, '.keep'), 'wb'):
                        pass
    else:
        with open(os.path.join(path, '.keep'), 'wb'):
            pass
    return
