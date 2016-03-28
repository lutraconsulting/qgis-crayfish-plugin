# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2015 Lutra Consulting

# info at lutraconsulting dot co dot uk
# Lutra Consulting
# 23 Chestnut Close
# Burgess Hill
# West Sussex
# RH15 8HN

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import ConfigParser
import os
import platform
import time
import urllib2
import zipfile

from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QCursor, QMessageBox, qApp

# Base URL for downloading of prepared binaries
downloadBaseUrl = 'http://www.lutraconsulting.co.uk/'
#downloadBaseUrl = 'http://localhost:8000/'  # for testing


def plugin_version_str():
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), '..', 'metadata.txt'))
    return cfg.get('general', 'version')

def plugin_version():
    ver_lst = plugin_version_str().split('.')
    ver = 0
    if len(ver_lst) >= 1:
        ver_major = int(ver_lst[0])
        ver |= ver_major << 16
    if len(ver_lst) >= 2:
        ver_minor = int(ver_lst[1])
        ver |= ver_minor << 8
    if len(ver_lst) == 3:
        ver_bugfix = int(ver_lst[2])
        ver |= ver_bugfix
    return ver


crayfish_zipfile = 'crayfish-lib-%s.zip' % plugin_version_str()


def ensure_library_installed(parent_widget=None):

    # Try to import the binary library:
    restartRequired = False

    platformVersion = platform.system()
    if platformVersion == 'Windows':
        while not extractBinPackageAfterRestart():
            reply = QMessageBox.critical(parent_widget,
              'Crayfish Installation Issue',
              "Crayfish plugin is unable to replace previous version of library. "
              "This is most likely caused by other QGIS instance running "
              "in the background. Please close other instances and try again.",
              QMessageBox.Retry | QMessageBox.Abort, QMessageBox.Retry)
            if reply != QMessageBox.Retry:
                return False

    try:
        from .. import crayfish
        assert crayfish.version() == plugin_version()
        return True   # everything's good - we are done here!
    except (OSError, AssertionError):
        pass  # ok we have a problem (no library or an old one)

    # The crayfishviewer binary cannot be found
    reply = QMessageBox.question(parent_widget,
          'Crayfish Viewer Library Not Found',
          "Crayfish Viewer depends on a platform specific compiled library "
          "which was not found. Would you like to attempt to automatically "
          "download and install one from the developer's website?",
          QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    if reply != QMessageBox.Yes:
        # User did not want to download
        QMessageBox.critical(parent_widget,
          'No Crayfish Viewer Library',
          "Crayfish Viewer relies on the Crayfish Viewer library.  Either "
          "download a library for your platform or download the source code "
          "from GitHub and build the library yourself.  Crayfish Viewer will "
          "now be disabled.")
        return False

    # Determine where to extract the files
    if platform.architecture()[0] == '64bit':
        platformVersion += '64'
    packageUrl = 'resources/crayfish/viewer/binaries/%s/%s' % (platformVersion, crayfish_zipfile)
    packageUrl = downloadBaseUrl + urllib2.quote(packageUrl)

    # Download it
    try:
        filename = os.path.join(os.path.dirname(__file__), crayfish_zipfile)
        downloadBinPackage(packageUrl, filename)
    except IOError, err:
        QMessageBox.critical(parent_widget,
          'Could Not Download Library',
          "The library for your platform could not be found on the developer's "
          "website.  Please see the About section for details of how to compile "
          "your own library or how to contact us for assistance.\n\n"
          "(Error: %s)" % str(err))
        return False

    # check whether we need to download GDAL library extra (on older QGIS installs
    # there is older version than the one required by the compiled binary)
    if platformVersion == 'Windows':
        downloadExtraLibs(parent_widget)

    # try to extract the downloaded file - may require a restart if the files exist already
    if not extractBinPackage(filename):
        QMessageBox.information(parent_widget,
          'Restart Required',
          "QGIS needs to be restarted in order to complete an update to the Crayfish "
          "Viewer Library.  Please restart QGIS.")
        return False

    # now try again
    from .. import crayfish
    QMessageBox.information(parent_widget, 'Succeeded', "Download and installation successful." )
    return True


def downloadBinPackage(packageUrl, destinationFileName):
    s = QSettings()
    # FIXME - does this work from behind a proxy?
    useProxy = s.value("proxy/proxyEnabled", False, type=bool)
    if useProxy:
        proxyHost = s.value("proxy/proxyHost", unicode())
        proxyPassword = s.value("proxy/proxyPassword", unicode())
        proxyPort = s.value("proxy/proxyPort", unicode())
        proxyType = s.value("proxy/proxyType", unicode())
        proxyTypes = { 'DefaultProxy' : 'http', 'HttpProxy' : 'http', 'Socks5Proxy' : 'socks', 'HttpCachingProxy' : 'http', 'FtpCachingProxy' : 'ftp' }
        if proxyType in proxyTypes: proxyType = proxyTypes[proxyType]
        proxyUser = s.value("proxy/proxyUser", unicode())
        proxyString = 'http://' + proxyUser + ':' + proxyPassword + '@' + proxyHost + ':' + proxyPort
        proxy = urllib2.ProxyHandler({proxyType : proxyString})
        auth = urllib2.HTTPBasicAuthHandler()
        opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
    conn = urllib2.urlopen(packageUrl)
    if os.path.isfile(destinationFileName):
        os.unlink(destinationFileName)
    destinationFile = open(destinationFileName, 'wb')
    destinationFile.write( conn.read() )
    destinationFile.close()


def extractBinPackage(destinationFileName):
    """ extract the downloaded package with .dll and .pyd files.
        If they already exist, the operation will fail because they are already loaded into Python.
        In such case we just keep a marker file 'EXTRACT_DLL' and extract it on the next run
    """
    destFolder = os.path.dirname(__file__)
    try:
        z = zipfile.ZipFile(destinationFileName)
        z.extractall(destFolder)
        z.close()
        return True
    except IOError:
        tmpF = open( os.path.join(destFolder, 'EXTRACT_DLL'), 'w' )
        tmpF.write(' ')
        tmpF.close()
        return False


def extractBinPackageAfterRestart():
    # Windows users may have opted to download a pre-compiled lib
    # In this case, if they already had the DLL loaded (they have
    # just uypdated) - they will need to restart QGIS to be able to
    # delete the old DLL
    destFolder = os.path.dirname(__file__)
    updateLibraryIndicator = os.path.join(destFolder, 'EXTRACT_DLL')
    if not os.path.isfile(updateLibraryIndicator):
        return True

    stillExists = True
    dllFileName = os.path.join(destFolder, 'crayfish.dll')
    for retryCount in range(3):
        try:
            os.unlink( dllFileName )
            stillExists = False
            break
        except WindowsError:
            time.sleep(3)

    if stillExists:
        return False

    destinationFileName = os.path.join(destFolder, crayfish_zipfile)
    z = zipfile.ZipFile(destinationFileName)
    z.extractall(destFolder)
    z.close()
    os.unlink(updateLibraryIndicator)
    return True


def downloadExtraLibs(parent_widget=None):
    try:
        from ctypes import windll
        x = windll.gdal111
        return True
    except WindowsError:
        pass # ok we need to download the libs

    try:
        QMessageBox.information(parent_widget,
          'Download Extra Libraries',
          "It is necessary to download newer GDAL library - this may take some "
          "time (~10MB), please wait.")
        qApp.setOverrideCursor(QCursor(Qt.WaitCursor))
        gdalFilename = os.path.join(os.path.dirname(__file__), 'gdal111.dll')
        gdalUrl = downloadBaseUrl+'resources/crayfish/viewer/binaries/Windows/extra/gdal111.dll'
        downloadBinPackage(gdalUrl, gdalFilename)
        qApp.restoreOverrideCursor()
        return True
    except IOError, err:
        qApp.restoreOverrideCursor()
        QMessageBox.critical(parent_widget,
          'Could Not Download Extra Libraries',
          "Download of the library failed. Please try again or contact us for "
          "further assistance.\n\n(Error: %s)" % str(err))
        return False


def downloadFfmpeg(parent_widget=None):

    destFolder = os.path.dirname(__file__)
    ffmpegZip = 'ffmpeg-20150505-git-6ef3426-win32-static.zip'
    ffmpegZipPath = os.path.join(destFolder, ffmpegZip)
    ffmpegUrl = downloadBaseUrl+'resources/crayfish/viewer/binaries/Windows/extra/'+ffmpegZip

    qApp.setOverrideCursor(QCursor(Qt.WaitCursor))
    try:
        downloadBinPackage(ffmpegUrl, ffmpegZipPath)
        z = zipfile.ZipFile(ffmpegZipPath)
        z.extractall(destFolder)
        z.close()
        os.unlink(ffmpegZipPath)
        qApp.restoreOverrideCursor()
        return os.path.join(destFolder, 'ffmpeg.exe')
    except IOError, err:
        qApp.restoreOverrideCursor()
        QMessageBox.critical(parent_widget,
          'Could Not Download FFmpeg',
          "Download of FFmpeg failed. Please try again or contact us for "
          "further assistance.\n\n(Error: %s)" % str(err))
