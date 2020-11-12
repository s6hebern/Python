# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------------------------------------------------
def installModuleArcpy(module):
    """
        Install a python module with arcpy into the standard ArcGIS installation
        :param module: module name as string
        :return: None

        :example: installModulArcpy('some_module')
    """

    import ctypes, subprocess
    from eomap import arcpy

    try:
        import module
        ctypes.windll.user32.MessageBoxA(0, 'Module ' + module + 'is already installed', 1)
    except:

        pyPath = 'C:\Python27\ArcGIS' + arcpy.GetInstallInfo()['Version'][0:4] + '\python'
        pipPath = 'C:\Python27\ArcGIS' + arcpy.GetInstallInfo()['Version'][0:4] + '\Scripts\pip'
        packPath = 'C:\Python27\ArcGIS' + arcpy.GetInstallInfo()['Version'][0:4] + '\Scripts\Lib'

        # upgrade pip to latest version, if necessary
        pip_v = subprocess.check_output([pipPath, '--version'])[4:10]
        pip_vInt = int(pip_v.split('.')[0] + pip_v.split('.')[1] + pip_v.split('.')[2])
        if pip_vInt <= 901:
            try:
                subprocess.call([pyPath, '-m', 'pip', 'install', '--upgrade', 'pip'])
            except:
                ctypes.windll.user32.MessageBoxA(0, \
                            'Cannot call "pip" to install required packages! \n'
                            'Normally, "pip" is installed together with ArcGIS \n'
                            'in "C:\Python27\ArcGIS[VERSION]\Scripts". \n'
                            'If it does not exist, try to reinstall ArcGIS and check again!', 'Error', 1)

        # try to import necessary modules, install if not installed yet
        try:
            import module
        except:
            subprocess.call([pipPath, 'install', '--user', str(module)])
            subprocess.call([pipPath, 'install', '--target=' + packPath, str(module)])

# ----------------------------------------------------------------------------------------------------------------------

def installModuleStandard(module):
    """
        Install a python module with arcpy into the standard ArcGIS installation
        :param module: module name as string
        :return: None

        :example: installModulStandard('some_module')
    """

    import ctypes, subprocess

    try:
        import module
        ctypes.windll.user32.MessageBoxA(0, 'Module ' + module + 'is already installed', 1)
    except:

        pyPath = 'C:\Python27\python'
        pipPath = 'C:\Python27\Scripts\pip'
        packPath = 'C:\Python27\Scripts\Lib'

        # upgrade pip to latest version, if necessary
        pip_v = subprocess.check_output([pipPath, '--version'])[4:10]
        pip_vInt = int(pip_v.split('.')[0] + pip_v.split('.')[1] + pip_v.split('.')[2])
        if pip_vInt <= 901:
            try:
                subprocess.call([pyPath, '-m', 'pip', 'install', '--upgrade', 'pip'])
            except:
                ctypes.windll.user32.MessageBoxA(0, \
                                                 'Cannot call "pip" to install required packages! \n'
                                                 'Normally, "pip" is installed together with Python \n'
                                                 'in "C:\Python27\Scripts". \n'
                                                 'If it does not exist, try to reinstall Python and check again!',
                                                 'Error', 1)

        # try to import necessary modules, install if not installed yet
        try:
            import module
        except:
            subprocess.call([pipPath, 'install', '--user', str(module)])
            subprocess.call([pipPath, 'install', '--target=' + packPath, str(module)])
