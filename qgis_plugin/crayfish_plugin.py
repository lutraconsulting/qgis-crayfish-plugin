# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import resources

import os

from crayfish_viewer_dock import CrayfishViewerDock

#from crayfish_viewer_plugin_layer import *
#from crayfish_viewer_plugin_layer_type import *
import crayfish_about_dialog

import platform
import urllib2
import os
import zipfile
import sip

class CrayfishPlugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.version = '0.1'
        self.dock = None
        self.dockInitialised = False # We have not yet created the dock
        self.lr = QgsMapLayerRegistry.instance()
        self.crayfishViewerLibFound = False
        
    def initGui(self):
        
        # Try to import the binary library:
        try:
            from crayfishviewer import CrayfishViewer
            self.crayfishViewerLibFound = True
        except ImportError:
            # The crayfishviewer binary cannot be found
            # FIXME - does this work from behind a proxy?
            reply = QMessageBox.question(self.iface.mainWindow(), 'Crayfish Viewer Library Not Found', "Crayfish Viewer depends on a platform specific compiled library which was not found.  Would you like to attempt to automatically download and install one from the developer's website?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                platformVersion = platform.system()
                libVersion = 'sip ' + sip.SIP_VERSION_STR + ' pyqt ' + PYQT_VERSION_STR
                crayfishVersion = self.version
                
                if platformVersion == 'Windows':
                    # Determine where to extract the files
                    destFolder = None
                    systemWidePluginPath = os.path.join(os.environ['OSGEO4W_ROOT'], 'apps', 'qgis', 'python', 'plugins', 'crayfish')
                    personalPluginPath = os.path.join(os.environ['HOMEPATH'], '.qgis', 'python', 'plugins', 'crayfish')
                    if os.path.isdir( systemWidePluginPath ):
                        destFolder = systemWidePluginPath
                    elif os.path.isdir(personalPluginPath):
                        destFolder = personalPluginPath
                    else:
                        QMessageBox.critical(self.iface.mainWindow(), 'Failed to Determine Installation Path', "The installation location for the Crayfish Viewer library could not be established.  Installation will not continue." )
                    if destFolder is not None:
                        packageUrl = 'resources/crayfish/viewer/binaries/' + platformVersion + '/' + libVersion + '/' + crayfishVersion + '/crayfish_viewer_library.zip'
                        packageUrl = 'http://www.lutraconsulting.co.uk/' + urllib2.quote(packageUrl)
                        destinationFileName = os.path.join(destFolder, 'crayfish_viewer_library.zip')
                        try:
                            s = QSettings()
                            useProxy = s.value("proxy/proxyEnabled").toBool()
                            if useProxy:
                                proxyHost = str(s.value("proxy/proxyHost").toString())
                                proxyPassword = str(s.value("proxy/proxyPassword").toString())
                                proxyPort = str(s.value("proxy/proxyPort").toString())
                                proxyType = str(s.value("proxy/proxyType").toString())
                                if proxyType == 'DefaultProxy':
                                    proxyType = 'http'
                                elif proxyType == 'HttpProxy':
                                    proxyType = 'http'
                                elif proxyType == 'Socks5Proxy':
                                    proxyType = 'socks'
                                elif proxyType == 'HttpCachingProxy':
                                    proxyType = 'http'
                                elif proxyType == 'FtpCachingProxy':
                                    proxyType = 'ftp'
                                proxyUser = str(s.value("proxy/proxyUser").toString())
                                proxyString = 'http://' + proxyUser + ':' + proxyPassword + '@' + proxyHost + ':' + proxyPort
                                proxy = urllib2.ProxyHandler({proxyType : proxyString})
                                auth = urllib2.HTTPBasicAuthHandler()
                                opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
                                urllib2.install_opener(opener)
                            conn = urllib2.urlopen(packageUrl)
                            destinationFile = open(destinationFileName, 'wb')
                            destinationFile.write( conn.read() )
                            destinationFile.close()

                            z = zipfile.ZipFile(destinationFileName)
                            z.extractall(destFolder)
                            from crayfishviewer import CrayfishViewer
                            self.crayfishViewerLibFound = True
                            QMessageBox.information(self.iface.mainWindow(), 'Succeeded', "Download and installation successful." )
                        except:
                            QMessageBox.critical(self.iface.mainWindow(), 'Download and Installation Failed', "Failed to download or install the Crayfish Viewer library." )
                else:
                    # Only windows is supported for the moment
                    QMessageBox.critical(self.iface.mainWindow(), 'Could Not Locate Appropriate Library', "A library for your platform could not be found on the developer's website.  Please see the About section for details of how to compile your own library or how to contact us for assistance." )
            else:
                # User did not want to download
                QMessageBox.critical(self.iface.mainWindow(), 'No Crayfish Viewer Library', "Crayfish Viewer relies on the Crayfish Viewer library.  Either download a library for your platform or download the source code from FIXME and build the library yourself.  Crayfish Viewer will now be disabled." )

        # Create action that will show the about page
        self.aboutAction = QAction(QIcon(":/plugins/crayfish/crayfish.png"), "About", self.iface.mainWindow())
        QObject.connect(self.aboutAction, SIGNAL("triggered()"), self.about)
        
        # Add menu item
        self.menu = self.iface.pluginMenu().addMenu(QIcon(":/plugins/crayfish/crayfish.png"), "Crayfish")
        self.menu.addAction(self.aboutAction)

        if not self.crayfishViewerLibFound:
            return
        
        # Create action that will load a layer to view
        self.action = QAction(QIcon(":/plugins/crayfish/crayfish_viewer_add_layer.png"), "Add Crayfish Layer", self.iface.mainWindow())
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        
        # Add toolbar button and menu item
        layerTB = self.iface.layerToolBar()
        layerTB.insertAction(self.iface.actionAddPgLayer(), self.action)
        
        # Add menu item
        self.menu.addAction(self.action)
        
        # Register plugin layer type
        from crayfish_viewer_plugin_layer_type import *
        QgsPluginLayerRegistry.instance().addPluginLayerType(CrayfishViewerPluginLayerType())
        
        # Make connections
        QObject.connect(self.lr, SIGNAL("layersWillBeRemoved(QStringList)"), self.layersRemoved)
        QObject.connect(self.lr, SIGNAL("layerWillBeRemoved(QString)"), self.layerRemoved)
        
        
    def layersRemoved(self, layers):
        for layer in layers:
            self.layerRemoved(layer)
    
    def layerRemoved(self, layer):
        """
            When a layer is removed, check if we have any crayfish layers left.
            If not, hide the dock
        """
        loadedCrayfishLayers = self.getCrayfishLayers()
        if len(loadedCrayfishLayers) == 0 and self.dock is not None:
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Calling Hide")
            self.dock.setHidden(True)

    def unload(self):
        if self.dock is not None:
            self.dock.close()
            self.iface.removeDockWidget(self.dock)
            
        self.menu.removeAction(self.aboutAction)
            
        if not self.crayfishViewerLibFound:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            return
        
        # Remove the plugin menu item and icon
        layerTB = self.iface.layerToolBar()
        layerTB.removeAction(self.action)
        # Remove menu item
        self.menu.removeAction(self.action)
        
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        
        # Unregister plugin layer type
        from crayfish_viewer_plugin_layer_type import *
        QgsPluginLayerRegistry.instance().removePluginLayerType(CrayfishViewerPluginLayer.LAYER_TYPE)
        
        # Make connections
        QObject.disconnect(self.lr, SIGNAL("layersWillBeRemoved(QStringList)"), self.layersRemoved)
        QObject.disconnect(self.lr, SIGNAL("layerWillBeRemoved(QString)"), self.layerRemoved)

    def run(self):
        """
            The user wants to view an Crayfish layer
            This layer could be either a .2dm file or a .dat file
            If a .dat file is loaded:
                That result is added to a layer already referencing its .2dm
                Or if no such layer exists, a new layer is created
        """
        
        # import pydevd; pydevd.settrace()
        
        # First get the file name of the 'thing' the user wants to view
        
        # Retrieve the last place we looked if stored
        settings = QSettings()
        lastFolder = str(settings.value("crayfishViewer/lastFolder", os.sep).toString())
        
        # Get the file name
        inFileName = QFileDialog.getOpenFileName(self.iface.mainWindow(), 'Open Crayfish Dat File', lastFolder, "DAT Results (*.dat);;2DM Mesh Files (*.2dm)")
        inFileName = str(inFileName)
        
        # Store the path we just looked in
        head, tail = os.path.split(inFileName)
        if head <> os.sep and head.lower() <> 'c:\\' and head <> '':
            settings.setValue("crayfishViewer/lastFolder", head)
        
        # Determine what type of file it is
        prefix, fileType = os.path.splitext(tail)
        fileType = fileType.lower()
        if fileType == '.2dm':
            """
                The user has selected a mesh file... add it if it is not already loaded
                
            """
            layerWith2dm = self.getLayerWith2DM(inFileName)
            
            if layerWith2dm is None:
                if not self.addLayer(inFileName):
                    # Failed to add this 2DM file
                    QMessageBox.critical(self.iface.mainWindow(), "Failed to Load Mesh", "Failed to load mesh file")
                    return
                else:
                    # 2DM loaded OK
                    return
            else:
                # This 2dm has already been added
                QMessageBox.information(self.iface.mainWindow(), "Mesh Already Present", "The mesh file you are trying to open is already loaded in layer " + layerWith2dm.name())
                return
        elif fileType == '.dat':
            """
                The user is adding a result set:
                    Determine its dat file name
                    If we have that layer open, add this result to the layer
                    Else create a new layer and add to that one
            """
            
            first, sep, last = inFileName.rpartition('_')
            meshFileName = first + '.2dm'
            parentLayer = self.getLayerWith2DM(meshFileName)
            if parentLayer is None:
                # The 2DM has not yet been loaded, load it
                if not self.addLayer(meshFileName):
                    QMessageBox.critical(self.iface.mainWindow(), "Failed to Load Mesh", "The mesh file associated with this DAT file (" + meshFileName + ") could not be loaded")
                    return
                parentLayer = self.getLayerWith2DM(meshFileName)
                assert( parentLayer is not None)
            if not parentLayer.provider.loadDataSet( QString(inFileName) ):
                QMessageBox.critical(self.iface.mainWindow(), "Failed to Load DAT", "Failed to successfully load the .Dat file")
            self.dock.refresh()
            self.dock.showMostRecentDataSet()
        else:
            # This is an unsupported file type
            QMessageBox.critical(self.iface.mainWindow(), "Unsupported File Type", "The file type you are trying to load is not supported: " + fileType)
            return
        

    def about(self):
        d = crayfish_about_dialog.CrayfishAboutDialog(self.iface)
        d.show()
        res = d.exec_()

    
    def getCrayfishLayers(self):
        crayfishLayers = []
        layers = self.iface.mapCanvas().layers()
        for l in layers:
            if l.type() == QgsMapLayer.PluginLayer and str(l.pluginLayerType()) == 'crayfish_viewer':
                crayfishLayers.append(l)
        return crayfishLayers
    
    
    def have2DM(self, fileName):
        
        layers = self.getCrayfishLayers()
        for layer in layers:
            if layer.twoDMFileName == fileName:
                return True
        return False
        
    def getLayerWith2DM(self, fileName):
        layers = self.getCrayfishLayers()
        for layer in layers:
            if layer.twoDMFileName == fileName:
                return layer
        return None
    
    def addLayer(self, twoDMFileName):
        from crayfish_viewer_plugin_layer import *
        layer = CrayfishViewerPluginLayer(twoDMFileName)
        if not layer.isValid():
            # Failed to load 2DM
            return False
            
        # Properly set the extents
        e = layer.provider.getExtents()
        r = QgsRectangle(   QgsPoint( e.bottomLeft().x(), e.bottomLeft().y() ),
                            QgsPoint( e.topRight().x(), e.topRight().y() ) )
        layer.setExtent( r )
        
        # Add to layer registry
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        
        layer.set2DMFileName(twoDMFileName) # Set the 2dm file name
        
        # Initiate the dock if this has not already been done
        if not self.dockInitialised:
            self.initialiseDock()
            self.dockInitialised = True
            layer.setDock(self.dock)
        self.dock.setHidden(False)
            
        head, tail = os.path.split(twoDMFileName)
        layerName, ext = os.path.splitext(tail)
        layer.setLayerName(layerName)
            
        self.dock.refresh()
        self.dock.listWidget_2.setFocus()
                
        return True
        
    
    def initialiseDock(self):
        
        self.dock = CrayfishViewerDock(self.iface)
        # QObject.connect(self.dock, SIGNAL('visibilityChanged(bool)'), self.showHideDockWidget) # nessisary ?
        self.iface.addDockWidget( Qt.LeftDockWidgetArea, self.dock )
        
        
        
