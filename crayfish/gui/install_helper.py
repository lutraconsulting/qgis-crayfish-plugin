# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2016 Lutra Consulting

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

import os
import time
import urllib2
import zipfile

from PyQt4.QtCore import Qt, QUrl, QEventLoop
from PyQt4.QtGui import QCursor, QMessageBox, qApp
from PyQt4.QtNetwork import QNetworkRequest
from qgis.core import QgsNetworkAccessManager

from ..core import load_library, VersionError, libpath
from ..buildinfo import findPlatformVersion, crayfish_zipfile

# Base URL for downloading of prepared binaries
downloadBaseUrl = 'https://www.lutraconsulting.co.uk/'
#downloadBaseUrl = 'http://localhost:8000/'  # for testing

destFolder = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))

def ensure_library_installed(parent_widget=None):

    # Try to import the binary library:
    restartRequired = False

    platformVersion = findPlatformVersion()

    while not extractBinPackageAfterRestart():
            reply = QMessageBox.critical(parent_widget,
              'Crayfish Installation Issue',
              "Crayfish plugin is unable to replace previous version of library. "
              "This is most likely caused by other QGIS instance running "
              "in the background. Please close other instances and try again.",
              QMessageBox.Retry | QMessageBox.Abort, QMessageBox.Retry)
            if reply != QMessageBox.Retry:
                return False

    version_error = False  # to see if there is already existing incompatible version

    try:
        load_library()
        return True   # everything's good - we are done here!
    except VersionError:
        version_error = True  # we have a problem - incompatible version
    except OSError:
        pass  # ok we have a problem (no library or it failed to load - e.g. 32/64bit mismatch)

    # The crayfishviewer binary cannot be found
    reply = QMessageBox.question(parent_widget,
          'Crayfish Library Not Found',
          "Crayfish depends on a platform specific compiled library "
          "which was not found. Would you like to attempt to automatically "
          "download and install one from the developer's website?",
          QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    if reply != QMessageBox.Yes:
        # User did not want to download
        QMessageBox.critical(parent_widget,
          'No Crayfish Library',
          "Crayfish relies on the Crayfish library.  Either "
          "download a library for your platform or download the source code "
          "from GitHub and build the library yourself.  Crayfish will "
          "now be disabled.")
        return False

    # Determine where to extract the files
    packageUrl = 'products/crayfish/viewer/binaries/%s/%s' % (platformVersion, crayfish_zipfile())
    packageUrl = downloadBaseUrl + urllib2.quote(packageUrl)

    # Download it
    try:
        filename = os.path.join(destFolder, crayfish_zipfile())
        downloadBinPackage(packageUrl, filename)
    except IOError, err:
        QMessageBox.critical(parent_widget,
          'Could Not Download Library',
          "The library for your platform could not be found on the developer's "
          "website.  Please see the About section for details of how to compile "
          "your own library or how to contact us for assistance.\n\n"
          "(Error: %s)" % str(err))
        return False

    success_msg = "Download and installation successful."
    restart_msg = "QGIS needs to be restarted in order to complete " + \
            "an update to the Crayfish Library.  Please restart QGIS."

    # do not rewrite the library - it is already loaded and it would cause havoc
    if version_error:
        addExtractLibraryMarker()
        QMessageBox.information(parent_widget, 'Download complete', success_msg + "\n\n" + restart_msg)
        return False

    # try to extract the downloaded file - may require a restart if the files exist already
    if not extractBinPackage(filename):
        QMessageBox.information(parent_widget, 'Download complete', success_msg + "\n\n" + restart_msg)
        return False

    QMessageBox.information(parent_widget, 'Download complete', success_msg)

    # now try again
    load_library()
    return True

def downloadBinPackage(packageUrl, destinationFileName):
    request = QNetworkRequest(QUrl(packageUrl))
    request.setRawHeader('Accept-Encoding', 'gzip,deflate')

    reply = QgsNetworkAccessManager.instance().get(request)
    evloop = QEventLoop()
    reply.finished.connect(evloop.quit)
    evloop.exec_(QEventLoop.ExcludeUserInputEvents)
    content_type = reply.rawHeader('Content-Type')
    if bytearray(content_type) == bytearray('application/zip'):
        if os.path.isfile(destinationFileName):
            os.unlink(destinationFileName)

        destinationFile = open(destinationFileName, 'wb')
        destinationFile.write(bytearray(reply.readAll()))
        destinationFile.close()
    else:
        ret_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        raise IOError("{} {}".format(ret_code, packageUrl))

def extractBinPackage(destinationFileName):
    """ extract the downloaded package with .dll and .pyd files.
        If they already exist, the operation will fail because they are already loaded into Python.
        In such case we just keep a marker file 'EXTRACT_DLL' and extract it on the next run
    """
    try:
        z = zipfile.ZipFile(destinationFileName)
        z.extractall(destFolder)
        z.close()
        return True
    except IOError:
        addExtractLibraryMarker()
        return False

def addExtractLibraryMarker():
    tmpF = open( os.path.join(destFolder, 'EXTRACT_DLL'), 'w' )
    tmpF.write(' ')
    tmpF.close()

def extractBinPackageAfterRestart():
    # Windows users may have opted to download a pre-compiled lib
    # In this case, if they already had the DLL loaded (they have
    # just uypdated) - they will need to restart QGIS to be able to
    # delete the old DLL
    updateLibraryIndicator = os.path.join(destFolder, 'EXTRACT_DLL')
    if not os.path.isfile(updateLibraryIndicator):
        return True

    stillExists = True
    for retryCount in range(3):
        try:
            os.unlink(libpath)
            stillExists = False
            break
        except OSError:
            time.sleep(3)

    if stillExists:
        return False

    destinationFileName = os.path.join(destFolder, crayfish_zipfile())
    z = zipfile.ZipFile(destinationFileName)
    z.extractall(destFolder)
    z.close()
    os.unlink(updateLibraryIndicator)
    return True

def downloadFfmpeg(parent_widget=None):

    ffmpegZip = 'ffmpeg-20150505-git-6ef3426-win32-static.zip'
    ffmpegZipPath = os.path.join(destFolder, ffmpegZip)
    ffmpegUrl = downloadBaseUrl+'products/crayfish/viewer/binaries/'+findPlatformVersion()+'/extra/'+ffmpegZip

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
