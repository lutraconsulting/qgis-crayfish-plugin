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
import zipfile

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtNetwork import QNetworkRequest
from qgis.core import QgsNetworkAccessManager

from ..buildinfo import findPlatformVersion

# Base URL for downloading of prepared binaries
downloadBaseUrl = 'https://www.lutraconsulting.co.uk/'
#downloadBaseUrl = 'http://localhost:8000/'  # for testing

destFolder = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))

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
    except IOError as err:
        qApp.restoreOverrideCursor()
        QMessageBox.critical(parent_widget,
          'Could Not Download FFmpeg',
          "Download of FFmpeg failed. Please try again or contact us for "
          "further assistance.\n\n(Error: %s)" % str(err))
