import ConfigParser
import os
import platform

def plugin_version_str():
    """ Return version of Python plugin from metadata as a string """
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))
    return cfg.get('general', 'version')

def findPlatformVersion():
    platformVersion = platform.system()

    if platformVersion == 'Linux':
        if (platform.linux_distribution()[0] == 'Ubuntu') and (float(platform.linux_distribution()[1]) >= 15.10):
            platformVersion = 'xenial'
        elif (platform.linux_distribution()[0] == 'Fedora'):
            platformVersion = 'fedora'

    if platform.architecture()[0] == '64bit':
        platformVersion += '64'
    return platformVersion

def crayfish_zipfile():
    return 'crayfish-lib-%s.zip' % plugin_version_str()

def crayfish_libname():
    if platform.system() == "Windows":
        return "crayfish.dll"
    elif platform.system() == "Linux":
        return "libcrayfish.so.1"
    else:
        return "libcrayfish.1.0.0.dylib"
