# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2014 Lutra Consulting

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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from crayfish_gui_utils import QgsMessageBar, qgis_message_bar

import resources

from crayfish_viewer_dock import CrayfishViewerDock

#from crayfish_viewer_plugin_layer import *
#from crayfish_viewer_plugin_layer_type import *
import crayfish_about_dialog
import crayfish_export_config_dialog
import crayfish_install_helper
import crayfish_animation_dialog

from illuvis import upload_dialog

import os
import sys


class CrayfishPlugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.dock = None
        self.lr = QgsMapLayerRegistry.instance()
        self.crayfishViewerLibFound = False

    def initGui(self):

        # Create action that will show the about page
        self.aboutAction = QAction(QIcon(":/plugins/crayfish/crayfish.png"), "About", self.iface.mainWindow())
        QObject.connect(self.aboutAction, SIGNAL("triggered()"), self.about)

        # Create action for upload
        self.uploadAction = QAction(QIcon(":/plugins/illuvis/illuvis_u_32w.png"), "Upload to illuvis ...", self.iface.mainWindow())
        QObject.connect(self.uploadAction, SIGNAL("triggered()"), self.upload)

        # Add menu items
        self.menu = self.iface.pluginMenu().addMenu(QIcon(":/plugins/crayfish/crayfish.png"), "Crayfish")
        self.menu.addAction(self.aboutAction)
        self.menu.addAction(self.uploadAction)

        if not crayfish_install_helper.ensure_library_installed():
          return

        self.crayfishViewerLibFound = True

        # Create action that will load a layer to view
        self.action = QAction(QIcon(":/plugins/crayfish/crayfish_viewer_add_layer.png"), "Add Crayfish Layer", self.iface.mainWindow())
        QObject.connect(self.action, SIGNAL("triggered()"), self.addCrayfishLayer)

        self.actionExportGrid = QAction(QIcon(":/plugins/crayfish/crayfish_export_raster.png"), "Export to Raster Grid ...", self.iface.mainWindow())
        QObject.connect(self.actionExportGrid, SIGNAL("triggered()"), self.exportGrid)

        self.actionExportAnimation = QAction(QIcon(":/plugins/crayfish/icon_video.png"), "Export Animation ...", self.iface.mainWindow())
        QObject.connect(self.actionExportAnimation, SIGNAL("triggered()"), self.exportAnimation)

        # Add toolbar button and menu item
        layerTB = self.iface.layerToolBar()
        layerTB.insertAction(self.iface.actionAddPgLayer(), self.action)

        # Add menu item
        self.menu.addAction(self.action)
        self.menu.addAction(self.actionExportGrid)
        self.menu.addAction(self.actionExportAnimation)

        # Register plugin layer type
        from crayfish_viewer_plugin_layer_type import CrayfishViewerPluginLayerType
        self.lt = CrayfishViewerPluginLayerType()
        QgsPluginLayerRegistry.instance().addPluginLayerType(self.lt)

        # Register actions for context menu
        self.iface.legendInterface().addLegendLayerAction(self.actionExportGrid, '', '', QgsMapLayer.PluginLayer, False)
        self.iface.legendInterface().addLegendLayerAction(self.uploadAction, '', '', QgsMapLayer.PluginLayer, False)
        self.iface.legendInterface().addLegendLayerAction(self.actionExportAnimation, '', '', QgsMapLayer.PluginLayer, False)

        # Make connections
        QObject.connect(self.lr, SIGNAL("layersWillBeRemoved(QStringList)"), self.layersRemoved)
        QObject.connect(self.lr, SIGNAL("layerWillBeRemoved(QString)"), self.layerRemoved)
        QObject.connect(self.lr, SIGNAL("layerWasAdded(QgsMapLayer*)"), self.layerWasAdded)

        # Create the dock widget
        self.dock = CrayfishViewerDock(self.iface)
        self.iface.addDockWidget( Qt.LeftDockWidgetArea, self.dock )
        self.dock.hide()   # do not show the dock by default
        QObject.connect(self.dock, SIGNAL("visibilityChanged(bool)"), self.dockVisibilityChanged)
        self.dock.treeDataSets.setCustomActions([self.actionExportGrid, self.uploadAction, self.actionExportAnimation])

        # Register data items provider (if possible - since 2.10)
        self.dataItemsProvider = None
        if 'QgsDataItemProvider' in globals():
          from crayfish_data_items import CrayfishDataItemProvider
          self.dataItemsProvider = CrayfishDataItemProvider()
          QgsDataItemProviderRegistry.instance().addProvider(self.dataItemsProvider)




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
            self.dock.hide()

    def unload(self):
        if self.dock is not None:
            if self.dock.plot_dock_widget is not None:
                self.dock.plot_dock_widget.close()
                self.iface.removeDockWidget(self.dock.plot_dock_widget)
            self.dock.close()
            self.iface.removeDockWidget(self.dock)

        self.menu.removeAction(self.aboutAction)
        self.menu.removeAction(self.uploadAction)

        if not self.crayfishViewerLibFound:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            return

        self.iface.legendInterface().removeLegendLayerAction(self.actionExportGrid)
        self.iface.legendInterface().removeLegendLayerAction(self.uploadAction)
        self.iface.legendInterface().removeLegendLayerAction(self.actionExportAnimation)

        # Remove the plugin menu item and icon
        layerTB = self.iface.layerToolBar()
        layerTB.removeAction(self.action)
        # Remove menu item
        self.menu.removeAction(self.action)
        self.menu.removeAction(self.actionExportGrid)
        self.menu.removeAction(self.actionExportAnimation)

        self.iface.pluginMenu().removeAction(self.menu.menuAction())

        # Unregister plugin layer type
        from crayfish_viewer_plugin_layer import CrayfishViewerPluginLayer
        QgsPluginLayerRegistry.instance().removePluginLayerType(CrayfishViewerPluginLayer.LAYER_TYPE)

        # Unregister data item provider
        if self.dataItemsProvider is not None:
          QgsDataItemProviderRegistry.instance().removeProvider(self.dataItemsProvider)
          self.dataItemsProvider = None

        # Make connections
        QObject.disconnect(self.lr, SIGNAL("layersWillBeRemoved(QStringList)"), self.layersRemoved)
        QObject.disconnect(self.lr, SIGNAL("layerWillBeRemoved(QString)"), self.layerRemoved)
        QObject.disconnect(self.lr, SIGNAL("layerWasAdded(QgsMapLayer*)"), self.layerWasAdded)

    def lastFolder(self):

        # Retrieve the last place we looked if stored
        settings = QSettings()
        try:
            return settings.value("crayfishViewer/lastFolder").toString()
        except AttributeError:  # QGIS 2
            return settings.value("crayfishViewer/lastFolder")

    def setLastFolder(self, path):
        if path <> os.sep and path.lower() <> 'c:\\' and path <> '':
            settings = QSettings()
            settings.setValue("crayfishViewer/lastFolder", path)

    def addCrayfishLayer(self):
        """
            The user wants to view an Crayfish layer
            This layer could be either a .2dm file or a .dat file
            If a .dat file is loaded:
                That result is added to a layer already referencing its .2dm
                Or if no such layer exists, a new layer is created
        """

        # First get the file name of the 'thing' the user wants to view

        # Get the file name
        inFileName = QFileDialog.getOpenFileName(self.iface.mainWindow(),
                                                 'Open Crayfish Dat File',
                                                 self.lastFolder(),
                                                 "Results Files DAT, SOL, XMDF, GRIB, netCFD (*.dat *.sol *.xmdf *.sww *.grb *.bin *.grib *.grib1 *.grib2 *.nc);;2DM Mesh Files (*.2dm)")
        inFileName = unicode(inFileName)
        if len(inFileName) == 0: # If the length is 0 the user pressed cancel
            return

        # Store the path we just looked in
        head, tail = os.path.split(inFileName)
        self.setLastFolder(head)

        # Determine what type of file it is
        prefix, fileType = os.path.splitext(tail)
        fileType = fileType.lower()
        if (fileType == '.2dm' or
            fileType == '.sww' or
            fileType == '.grb' or fileType == '.bin' or fileType == '.grib' or fileType == '.grib1' or fileType == '.grib2' or
            fileType == '.nc'):
            """
                The user has selected a mesh file...
            """
            if not self.loadMesh(inFileName, fileType):
                return

            # update GUI
            self.dock.currentLayerChanged()

        elif fileType == '.dat' or fileType == '.sol' or fileType == '.xmdf':
            """
                The user has selected a results-only file...
            """
            self.loadDatFile(inFileName)

        else:
            # This is an unsupported file type
            qgis_message_bar.pushMessage("Crayfish", "The file type you are trying to load is not supported: " + fileType, level=QgsMessageBar.CRITICAL)
            return

    def loadMesh(self, inFileName, fileType):
        # Load mesh as new Crayfish layer for file
        # In file is container of multiple meshes, load them all separately (e.g. netCFD file)
        data_sources_to_add = [inFileName]
        if fileType == '.nc':
            # this one is container of multiple sublayers
            temp_raster = QgsRasterLayer(inFileName)
            if (not temp_raster.isValid()) and (len(temp_raster.subLayers()) > 1):
                data_sources_to_add = temp_raster.subLayers()

        for data_source in data_sources_to_add:
            layerWith2dm = self.getLayerWith2DM(data_source)

            if layerWith2dm:
                # This 2dm has already been added
                qgis_message_bar.pushMessage("Crayfish", "The mesh file is already loaded in layer " + layerWith2dm.name(), level=QgsMessageBar.INFO)
                return False

            if not self.addLayer(data_source):
                return False # addLayer() reports errors/warnings

        return True # success

    def loadMeshForFile(self, inFileName):

        # if there is a selected Crayfish layer, use the mesh
        currCrayfishLayer = self.dock.currentCrayfishLayer()
        if currCrayfishLayer:
          return currCrayfishLayer

        # if no crayfish layer is selected, try to guess the mesh file name
        if inFileName.lower().endswith(".xmdf"):
          # for XMDF assume the same filename, just different extension for mesh
          first = inFileName[:-5]
        else:
          # for DAT assume for abc_def.dat the mesh is abc.2dm
          # maybe we need more rules for guessing 2dm for different solvers
          first, sep, last = inFileName.rpartition('_')
        meshFileName = first + '.2dm'

        parentLayer = self.getLayerWith2DM(meshFileName)
        if parentLayer is not None:
            return parentLayer   # already loaded

        # The 2DM has not yet been loaded, load it

        # check whether the file exists
        if not os.path.exists(meshFileName):

            # compatibility for QGIS 1.x
            if not hasattr(self.iface, "messageBar"):
                res = QMessageBox.question(None, "Crayfish", "The mesh file does not exist:\n"+meshFileName+"\nWould you like to locate it manually?", QMessageBox.Yes|QMessageBox.No)
                if res != QMessageBox.Yes:
                    return
                self.locateMeshForFailedDatFile(inFileName)
                return

            # QGIS >= 2.0
            self.lastFailedWidget = self.iface.messageBar().createMessage("Crayfish", "The mesh file does not exist ("+meshFileName+")")
            self.lastFailedWidget._inFileName = inFileName
            button = QPushButton("Locate", self.lastFailedWidget)
            button.pressed.connect(self.locateMeshForFailedDatFile)
            self.lastFailedWidget.layout().addWidget(button)
            self.iface.messageBar().pushWidget(self.lastFailedWidget, QgsMessageBar.CRITICAL)
            return

        if not self.addLayer(meshFileName):
            return    # errors/warnings reported in addLayer()

        parentLayer = self.getLayerWith2DM(meshFileName)
        assert( parentLayer is not None)
        return parentLayer


    def loadDatFile(self, inFileName, parentLayer=None):
        """
            The user is adding a result set:
                Determine its dat file name
                If we have that layer open, add this result to the layer
                Else create a new layer and add to that one
        """

        if not parentLayer:
            parentLayer = self.loadMeshForFile(inFileName)
            if not parentLayer:
                return   # error message has been shown already

        if parentLayer.isDataSetLoaded(inFileName):
            qgis_message_bar.pushMessage("Crayfish", "The data file is already loaded in layer " + parentLayer.name(), level=QgsMessageBar.INFO)
            return

        dsCountBefore = parentLayer.mesh.dataset_count()

        # try to load it as binary file, if not successful, try as ASCII format
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            parentLayer.mesh.load_data( inFileName )
            QApplication.restoreOverrideCursor()
        except ValueError:
            QApplication.restoreOverrideCursor()
            import crayfish
            err = crayfish.last_load_status()[0]
            # reuse from showMeshLoadError
            err_msgs = {
              crayfish.Err_NotEnoughMemory : 'Not enough memory',
              crayfish.Err_FileNotFound : 'Unable to read the file - missing file or no read access',
              crayfish.Err_UnknownFormat : 'File format not recognized',
              crayfish.Err_IncompatibleMesh : 'Mesh is not compatible'
            }
            msg = "Failed to load the data file"
            if err in err_msgs:
              msg += " (%s)" % err_msgs[err]
            qgis_message_bar.pushMessage("Crayfish", msg, level=QgsMessageBar.CRITICAL)
            return

        dsCountAfter = parentLayer.mesh.dataset_count()

        for index in xrange(dsCountBefore, dsCountAfter):
            parentLayer.initCustomValues(parentLayer.mesh.dataset(index))

        # set to most recent data set (first one from the newly added datasets)
        parentLayer.current_ds_index = dsCountBefore
        # update GUI
        self.dock.currentLayerChanged()
        # allow user to go through the time steps with arrow keys
        self.dock.cboTime.setFocus()



    def locateMeshForFailedDatFile(self, datFileName=None):
        """ the user wants to specify the mesh file """

        inFileName = QFileDialog.getOpenFileName(self.iface.mainWindow(), 'Open Mesh File', self.lastFolder(), "2DM Mesh Files (*.2dm)")
        inFileName = unicode(inFileName)
        if len(inFileName) == 0: # If the length is 0 the user pressed cancel
            return

        if hasattr(self.iface, "messageBar"):  # QGIS >= 2.0 only
            datFileName = self.lastFailedWidget._inFileName
            # remove the widget from message bar
            self.iface.messageBar().popWidget(self.lastFailedWidget)
            del self.lastFailedWidget

        layerWith2dm = self.getLayerWith2DM(inFileName)
        if not layerWith2dm:
            layerWith2dm = self.addLayer(inFileName)
            if not layerWith2dm:
                return # addLayer() reports errors/warnings

        # mesh file is ready, now load the .dat file
        self.loadDatFile(datFileName, layerWith2dm)


    def about(self):
        d = crayfish_about_dialog.CrayfishAboutDialog(self.iface)
        d.show()
        res = d.exec_()


    def upload(self):
        d = upload_dialog.UploadDialog(self.iface, self.dock.currentCrayfishLayer())
        d.exec_()


    def getCrayfishLayers(self):
        crayfishLayers = []
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
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
        from crayfish_viewer_plugin_layer import CrayfishViewerPluginLayer
        layer = CrayfishViewerPluginLayer(twoDMFileName)
        if not layer.isValid():
            layer.showMeshLoadError(twoDMFileName)
            return None

        # Add to layer registry
        QgsMapLayerRegistry.instance().addMapLayer(layer)

        import crayfish
        warn = crayfish.last_load_status()[1]
        if warn == crayfish.Warn_UnsupportedElement:
                # Unsupported element seen
                qgis_message_bar.pushMessage("Crayfish", "The mesh contains elements that are unsupported at this time. The following types of elements will be ignored for the time being: E2L, E3L, E6T, E8Q, E9Q", level=QgsMessageBar.WARNING)
        elif warn == crayfish.Warn_InvalidElements:
                qgis_message_bar.pushMessage("Crayfish", "The mesh contains some invalid elements, they will not be rendered.", level=QgsMessageBar.WARNING)

        return layer

    def layerWasAdded(self, layer):
        if layer.type() != QgsMapLayer.PluginLayer:
            return
        if layer.LAYER_TYPE != 'crayfish_viewer':
            return

        # Add custom legend actions
        self.iface.legendInterface().addLegendLayerActionForLayer(self.actionExportGrid, layer)
        self.iface.legendInterface().addLegendLayerActionForLayer(self.uploadAction, layer)
        self.iface.legendInterface().addLegendLayerActionForLayer(self.actionExportAnimation, layer)

        # make sure the dock is visible and up-to-date
        self.dock.show()


    def dockVisibilityChanged(self, visible):
        if visible and len(self.getCrayfishLayers()) == 0:
            # force hidden on startup
            QTimer.singleShot(0, self.dock.hide)


    def exportGrid(self):
        """ export current layer's data to a raster grid """
        layer = self.dock.currentCrayfishLayer()
        if not layer:
            QMessageBox.warning(None, "Crayfish", "Please select a Crayfish layer for export")
            return

        mc = self.iface.mapCanvas()
        if mc.hasCrsTransformEnabled():
          if hasattr(mc, "mapSettings"):
            crsWkt = mc.mapSettings().destinationCrs().toWkt()
          else:
            crsWkt = mc.mapRenderer().destinationCrs().toWkt()
        else:
          crsWkt = layer.crs().toWkt()  # no OTF reprojection

        dlgConfig = crayfish_export_config_dialog.CrayfishExportConfigDialog()
        if not dlgConfig.exec_():
            return
        dlgConfig.saveSettings()

        filenameTIF = os.path.join(self.lastFolder(), layer.currentDataSet().name() + ".tif")
        filenameTIF = QFileDialog.getSaveFileName(None, "Export as Raster Grid", filenameTIF, "TIFF raster (*.tif)")
        if not filenameTIF:
            return

        self.setLastFolder(os.path.dirname(filenameTIF))

        try:
            res = layer.currentOutput().export_grid(dlgConfig.resolution(), filenameTIF, crsWkt)
        except OSError: # delayed loading of GDAL failed (windows only)
            QMessageBox.critical(None, "Crayfish", "Export failed due to incompatible "
              "GDAL library - try to upgrade your QGIS installation to a newer version.")
            return
        if not res:
            QMessageBox.critical(None, "Crayfish", "Failed to export to raster grid")
            return

        if dlgConfig.addToCanvas():
            name = os.path.splitext(os.path.basename(filenameTIF))[0]
            self.iface.addRasterLayer(filenameTIF, name, "gdal")

    def exportAnimation(self):
        """ export current layer's timesteps as an animation """
        layer = self.dock.currentCrayfishLayer()
        if not layer:
            QMessageBox.warning(None, "Crayfish", "Please select a Crayfish layer for export")
            return

        if self.dock.currentDataSet().output_count() < 2:
            QMessageBox.warning(None, "Crayfish", "Please use time-varying dataset for animation export")
            return

        dlg = crayfish_animation_dialog.CrayfishAnimationDialog(self.iface)
        dlg.exec_()
