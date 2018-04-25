import subprocess as sub


def callCmd(cmd):
    """
    Execute a commandline call via subprocess

    :param str cmd:
    :return: returncode
    :rtype: int
    """

    p = sub.Popen(cmd, stdout=sub.PIPE, stderr=sub.STDOUT)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print cmd
        print stdout
        print stderr
    return p.returncode
