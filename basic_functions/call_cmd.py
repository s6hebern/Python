import sys
import warnings
import subprocess as sub


def run_cmd(cmd, print_output=False, report_errors=True):
    # type: (list, bool, bool) -> int
    """
    Execute a commandline call via subprocess

    :param cmd: List of commandline parameters
    :param print_output: Print what the commandline returns as stdout
    :param report_errors: Print what the commandline returns as sterr
    :return: returncode
    """
    if not isinstance(cmd, list):
        warnings.warn('{c} is not a list! Please provide commandline arguments as Python list! '
                      'Trying to convert internally...'.format(c=cmd))
        try:
            cmd = cmd.split()
            print('OK!')
        except:
            raise TypeError('{c} is not a list! Please provide commandline arguments as Python '
                            'list!'.format(c=cmd))
    p = sub.Popen(cmd, stdout=sub.PIPE, stderr=sub.PIPE)
    stdout, stderr = p.communicate()
    if print_output:
        print(stdout)
    if report_errors and p.returncode != 0:
        print cmd
        print stdout
        print stderr
    return p.returncode


def cmd_to_powershell(command):
    # type: (list) -> list
    """
    Converts a normal shell command string into a command that runs in Windows PowerShell.
    Make sure the program you are calling has the program indicator set, like this: \n
    python "C:/Program Files/GDAL/gdal_merge.py" ... \n
    This is important, since the PowerShell does not know what program to use for which file extension
    (normal cmd does) \n
    --- \n
    :param command: String or list of strings of commandline arguments. Lists are always safer!
    :return (list): list object that can be directly passed to subprocess (...)
    --- \n
    Example: \n
    cmd = 'VERY LONG COMMAND LINE STRING HERE' \n
    if len(cmd) >= 8191:
        cmd = cmd2powershell.convert(cmd)
    """
    if 'win' not in sys.platform.lower():
        raise EnvironmentError('ERROR: You are not using a Windows environment!')
    if isinstance(command, str):
        warnings.warn('Command is given as a string! Converting it to list assuming space as a separator...')
    elif isinstance(command, list):
        pass
    else:
        raise TypeError('ERROR: Command is neither given as a list nor as a string!')
    
    def _warning(message, category=UserWarning, filename='', lineno=-1):
        print(message)
        
    warnings.showwarning = _warning
    if len(command) < 8191:
        warnings.warn('No need to convert to PowerShell command!')
        cmd_list = command
    else:
        warnings.warn('Command line string exceeds limit of 8191 characters! Using Windows PowerShell instead!')
        cmd_list = ['powershell.exe'] + command
    return cmd_list
