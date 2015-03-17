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


# Base URL for downloading of prepared binaries
downloadBaseUrl = 'http://www.lutraconsulting.co.uk/'
#downloadBaseUrl = 'http://localhost:8000/'  # for testing

def ensure_library_installed():
    try:
        import crayfish
        # TODO: check version
        return True
    except OSError:
        # TODO: try to download + install
        return False


def ensure_library_installed_old():

    # currently does nothing
    # TODO: re-enable
    return True

    # Try to import the binary library:
    restartRequired = False

    platformVersion = platform.system()
    if platformVersion == 'Windows':
        self.extractBinPackageAfterRestart()

    try:
        from crayfishviewer import CrayfishViewer
        from crayfishviewer import version as crayfishVersion
        assert self.version == str( crayfishVersion() )
        return True   # everything's good - we are done here!
    except (ImportError, AttributeError, AssertionError):
        pass  # ok we have a problem (no library or an old one)

    # The crayfishviewer binary cannot be found
    reply = QMessageBox.question(self.iface.mainWindow(),
          'Crayfish Viewer Library Not Found',
          "Crayfish Viewer depends on a platform specific compiled library "
          "which was not found. Would you like to attempt to automatically "
          "download and install one from the developer's website?",
          QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    if reply != QMessageBox.Yes:
        # User did not want to download
        QMessageBox.critical(self.iface.mainWindow(),
          'No Crayfish Viewer Library',
          "Crayfish Viewer relies on the Crayfish Viewer library.  Either "
          "download a library for your platform or download the source code "
          "from GitHub and build the library yourself.  Crayfish Viewer will "
          "now be disabled.")
        return False

    libVersion = 'sip ' + sip.SIP_VERSION_STR + ' pyqt ' + PYQT_VERSION_STR
    crayfishVersion = self.version

    # Determine where to extract the files
    if platform.architecture()[0] == '64bit':
        platformVersion += '64'
    packageUrl = 'resources/crayfish/viewer/binaries/' + platformVersion + '/' + libVersion + '/' + crayfishVersion + '/crayfish_viewer_library.zip'
    packageUrl = downloadBaseUrl + urllib2.quote(packageUrl)

    # Download it
    try:
        filename = os.path.join(os.path.dirname(__file__), 'crayfish_viewer_library.zip')
        self.downloadBinPackage(packageUrl, filename)
    except IOError, err:
        QMessageBox.critical(self.iface.mainWindow(),
          'Could Not Download Library',
          "The library for your platform could not be found on the developer's "
          "website.  Please see the About section for details of how to compile "
          "your own library or how to contact us for assistance.\n\n"
          "(Error: %s)" % str(err))
        return False

    # check whether we need to download GDAL library extra (on older QGIS installs
    # there is older version than the one required by the compiled binary)
    if platformVersion == 'Windows':
        downloadExtraLibs()

    # try to extract the downloaded file - may require a restart if the files exist already
    if not self.extractBinPackage(filename):
        QMessageBox.information(self.iface.mainWindow(),
          'Restart Required',
          "QGIS needs to be restarted in order to complete an update to the Crayfish "
          "Viewer Library.  Please restart QGIS.")
        return False

    # now try again
    from crayfishviewer import CrayfishViewer
    QMessageBox.information(self.iface.mainWindow(), 'Succeeded', "Download and installation successful." )
    return True


def downloadBinPackage(self, packageUrl, destinationFileName):
    s = QSettings()
    # FIXME - does this work from behind a proxy?
    try:
        useProxy = s.value("proxy/proxyEnabled", False).toBool()
    except:
        useProxy = s.value("proxy/proxyEnabled", False, type=bool)
    if useProxy:
        proxyHost = qv2unicode(s.value("proxy/proxyHost", unicode()))
        proxyPassword = qv2unicode(s.value("proxy/proxyPassword", unicode()))
        proxyPort = qv2unicode(s.value("proxy/proxyPort", unicode()))
        proxyType = qv2unicode(s.value("proxy/proxyType", unicode()))
        proxyTypes = { 'DefaultProxy' : 'http', 'HttpProxy' : 'http', 'Socks5Proxy' : 'socks', 'HttpCachingProxy' : 'http', 'FtpCachingProxy' : 'ftp' }
        if proxyType in proxyTypes: proxyType = proxyTypes[proxyType]
        proxyUser = qv2unicode(s.value("proxy/proxyUser", unicode()))
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


def extractBinPackage(self, destinationFileName):
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


def extractBinPackageAfterRestart(self):
    # Windows users may have opted to download a pre-compiled lib
    # In this case, if they already had the DLL loaded (they have
    # just uypdated) - they will need to restart QGIS to be able to
    # delete the old DLL
    destFolder = os.path.dirname(__file__)
    updateLibraryIndicator = os.path.join(destFolder, 'EXTRACT_DLL')
    if not os.path.isfile(updateLibraryIndicator):
        return

    dllFileName = os.path.join(destFolder, 'crayfishViewer.dll')
    pydFileName = os.path.join(destFolder, 'crayfishviewer.pyd')
    for retryCount in range(5):
        try:
            os.unlink( dllFileName )
            break
        except:
            time.sleep(3)

    os.unlink( pydFileName )
    destinationFileName = os.path.join(destFolder, 'crayfish_viewer_library.zip')
    z = zipfile.ZipFile(destinationFileName)
    z.extractall(destFolder)
    z.close()
    os.unlink(updateLibraryIndicator)


def downloadExtraLibs():
    try:
        from ctypes import windll
        x = windll.gdal111
        return True
    except WindowsError:
        pass # ok we need to download the libs

    try:
        QMessageBox.information(self.iface.mainWindow(),
          'Download Extra Libraries',
          "It is necessary to download newer GDAL library - this may take some "
          "time (~10MB), please wait.")
        qApp.setOverrideCursor(QCursor(Qt.WaitCursor))
        gdalFilename = os.path.join(os.path.dirname(__file__), 'gdal111.dll')
        gdalUrl = downloadBaseUrl+'resources/crayfish/viewer/binaries/'+platformVersion+'/extra/gdal111.dll'
        self.downloadBinPackage(gdalUrl, gdalFilename)
        qApp.restoreOverrideCursor()
        return True
    except IOError, err:
        qApp.restoreOverrideCursor()
        QMessageBox.critical(self.iface.mainWindow(),
          'Could Not Download Extra Libraries',
          "Download of the library failed. Please try again or contact us for "
          "further assistance.\n\n(Error: %s)" % str(err))
        return False
