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

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qgis.core import *
from .gui.plot_widget import CrayfishPlotWidget
from .gui.animation_dialog import CrayfishAnimationDialog
from .gui.trace_animation_dialog import CrayfishTraceAnimationDialog
from .gui.utils import mesh_layer_active_dataset_group_with_maximum_timesteps, isLayer1d, isLayer2d, isLayer3d
from .processing import CrayfishProcessingProvider
from .resources import *

class CrayfishPlugin:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.plot_dock_widget = None
        self.plot_dock_3d_widget = None
        self.plot_dock_1d_widget = None
        self.provider = CrayfishProcessingProvider()

        self.action1DPlot = None
        self.action2DPlot = None
        self.action3DPlot = None

        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().layersAdded.connect(self.updateActionEnabled)
        QgsProject.instance().layersRemoved.connect(self.updateActionEnabled)
        self.layers_added(QgsProject.instance().mapLayers().values())

    def initGui(self):
        # Add menu items
        self.mesh_menu = self.iface.mainWindow().findChild(QMenu, 'mMeshMenu')
        self.menu = self.mesh_menu.addMenu(QIcon(":/plugins/crayfish/images/crayfish.png"), "Crayfish")

        self.action1DPlot = QAction(QIcon(":/plugins/crayfish/images/icon_plot_1d.svg"),"1D Plot", self.iface.mainWindow())
        self.action1DPlot.triggered.connect(self.toggle_1d_plot)

        self.action2DPlot = QAction(QIcon(":/plugins/crayfish/images/icon_plot.svg"), "2D Plot", self.iface.mainWindow())
        self.action2DPlot.triggered.connect(self.toggle_plot)

        self.action3DPlot = QAction(QIcon(":/plugins/crayfish/images/icon_plot_3d.svg"), "3D Plot", self.iface.mainWindow())
        self.action3DPlot.triggered.connect(self.toggle_3d_plot)

        self.actionExportAnimation = QAction(QIcon(":/plugins/crayfish/images/icon_video.png"), "Export Animation ...", self.iface.mainWindow())
        self.actionExportAnimation.triggered.connect(self.exportAnimation)

        self.actionExportTraceAnimation=QAction(QIcon(":/plugins/crayfish/images/icon_video.png"),"Export Trace Animation ...", self.iface.mainWindow())
        self.actionExportTraceAnimation.triggered.connect(self.exportParticleTraceAnimation)

        self.menu.addAction(self.action1DPlot)
        self.menu.addAction(self.action2DPlot)
        self.menu.addAction(self.action3DPlot)
        self.menu.addAction(self.actionExportAnimation)
        self.menu.addAction(self.actionExportTraceAnimation)

        # Register actions for context menu
        self.iface.addCustomActionForLayerType(self.action1DPlot, '', QgsMapLayer.MeshLayer, False)
        self.iface.addCustomActionForLayerType(self.action2DPlot, '', QgsMapLayer.MeshLayer, False)
        self.iface.addCustomActionForLayerType(self.action3DPlot, '', QgsMapLayer.MeshLayer, False)
        self.iface.addCustomActionForLayerType(self.actionExportAnimation, '', QgsMapLayer.MeshLayer, True)
        self.iface.addCustomActionForLayerType(self.actionExportTraceAnimation, '', QgsMapLayer.MeshLayer, True)

        # Make connections
        self.iface.layerTreeView().currentLayerChanged.connect(self.active_layer_changed)

        # Create widget
        self.plot_dock_widget = QDockWidget("Crayfish 2D Plot")
        self.plot_dock_widget.setObjectName("CrayfishPlotDock")
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_widget)
        w = CrayfishPlotWidget(self.plot_dock_widget)
        self.plot_dock_widget.setWidget(w)
        self.plot_dock_widget.hide()

        QgsApplication.processingRegistry().addProvider(self.provider)

        self.updateActionEnabled()

    def active_layer_changed(self, layer):
        # only change layer when there is none selected
        if self.plot_dock_widget.widget().layer:
            return

        # only assign layer when active layer is a mesh layer
        if layer and layer.type() == QgsMapLayer.MeshLayer:
            dataProvider=layer.dataProvider()
            if dataProvider.contains(QgsMesh.Face):
                self.plot_dock_widget.widget().set_layer(layer)

            if self.plot_dock_1d_widget is not None and dataProvider.contains(QgsMesh.Edge):
                self.plot_dock_1d_widget.widget().set_layer(layer)

            if self.plot_dock_3d_widget is not None and isLayer3d(layer):
                self.plot_dock_3d_widget.widget().set_layer(layer)

    def toggle_plot(self):
        self.plot_dock_widget.setVisible(not self.plot_dock_widget.isVisible())

    def toggle_3d_plot(self):

        if self.plot_dock_3d_widget is None:
            from .gui.plot_3d_widget import CrayfishPlot3dWidget
            # Create widget
            self.plot_dock_3d_widget = QDockWidget("Crayfish 3D Plot")
            self.plot_dock_3d_widget.setObjectName("CrayfishPlot3dDock")
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_3d_widget)
            w = CrayfishPlot3dWidget(self.plot_dock_3d_widget)
            self.plot_dock_3d_widget.setWidget(w)
            self.plot_dock_3d_widget.hide()

        self.plot_dock_3d_widget.setVisible(not self.plot_dock_3d_widget.isVisible())

    def toggle_1d_plot(self):

        if self.plot_dock_1d_widget is None:
            from .gui.plot_1d_widget import CrayfishPlot1dWidget
            # Create widget
            self.plot_dock_1d_widget = QDockWidget("Crayfish 1D Plot")
            self.plot_dock_1d_widget.setObjectName("CrayfishPlot1dDock")
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_1d_widget)
            w = CrayfishPlot1dWidget(self.plot_dock_1d_widget)
            self.plot_dock_1d_widget.setWidget(w)
            self.plot_dock_1d_widget.hide()

        self.plot_dock_1d_widget.setVisible(not self.plot_dock_1d_widget.isVisible())


    def unload(self):
        # Remove menu item
        self.menu.removeAction(self.action1DPlot)
        self.menu.removeAction(self.action2DPlot)
        self.menu.removeAction(self.action3DPlot)
        self.menu.removeAction(self.actionExportAnimation)
        self.menu.removeAction(self.actionExportTraceAnimation)

        # Remove actions for context menu
        self.iface.removeCustomActionForLayerType(self.action1DPlot)
        self.iface.removeCustomActionForLayerType(self.action2DPlot)
        self.iface.removeCustomActionForLayerType(self.action3DPlot)
        self.iface.removeCustomActionForLayerType(self.actionExportAnimation)
        self.iface.removeCustomActionForLayerType(self.actionExportTraceAnimation)

        # Remove menu
        self.mesh_menu.removeAction(self.menu.menuAction())
        self.menu = None

        # Remove connections
        self.iface.layerTreeView().currentLayerChanged.disconnect(self.active_layer_changed)

        # Remove widgets
        self.layer = None
        self.plot_dock_widget.close()
        self.iface.removeDockWidget(self.plot_dock_widget)
        self.plot_dock_widget = None

        if self.plot_dock_3d_widget is not None:
            self.plot_dock_3d_widget.close()
            self.iface.removeDockWidget(self.plot_dock_3d_widget)
            self.plot_dock_3d_widget = None

        if self.plot_dock_1d_widget is not None:
            self.plot_dock_1d_widget.close()
            self.iface.removeDockWidget(self.plot_dock_1d_widget)
            self.plot_dock_1d_widget = None

        QgsApplication.processingRegistry().removeProvider(self.provider)

    def exportAnimation(self):
        """ export current layer's timesteps as an animation """
        layer = self.iface.activeLayer()
        if not layer or layer.type() != QgsMapLayer.MeshLayer:
            QMessageBox.warning(None, "Crayfish", "Please select a Mesh Layer for export")
            return

        if not layer.dataProvider():
            QMessageBox.warning(None, "Crayfish", "Mesh layer has invalid data provider")
            return

        if not layer.temporalProperties().isActive():
            QMessageBox.warning(None, "Crayfish", "Mesh layer is not temporal")
            return

        grp = mesh_layer_active_dataset_group_with_maximum_timesteps(layer)
        if grp is None:
            QMessageBox.warning(None, "Crayfish", "Please activate contours or vector rendering for animation export")
            return
        elif layer.dataProvider().datasetCount(grp) < 2:
            QMessageBox.warning(None, "Crayfish", "Please  use time-varying dataset group for animation export")
            return

        dlg = CrayfishAnimationDialog(self.iface)
        dlg.exec_()

    def exportParticleTraceAnimation(self):
        layer=self.iface.activeLayer()
        if not layer or layer.type()!= QgsMapLayer.MeshLayer:
            QMessageBox.warning(None, "Crayfish", "Please select a Mesh Layer for export")
            return

        if not layer.dataProvider():
            QMessageBox.warning(None, "Crayfish", "Mesh layer has invalid data provider")
            return

        vectorDatasetGroup=layer.rendererSettings().activeVectorDatasetGroup()

        if vectorDatasetGroup < 0:
            QMessageBox.warning(None, "Crayfish", "Please activate vector rendering for trace animation export")
            return

        dlg = CrayfishTraceAnimationDialog(self.iface)
        dlg.exec_()

    def layers_added(self, lst):

        for layer in lst:
            if isLayer1d(layer) and self.action1DPlot is not None:
                self.iface.addCustomActionForLayer(self.action1DPlot, layer)
            if isLayer2d(layer) and self.action2DPlot is not None:
                self.iface.addCustomActionForLayer(self.action2DPlot, layer)
            if isLayer3d(layer) and self.action3DPlot is not None:
                self.iface.addCustomActionForLayer(self.action3DPlot, layer)

    def updateActionEnabled(self):
        layers = QgsProject.instance().mapLayers().values()

        enabled = len(layers)!=0
        self.actionExportAnimation.setEnabled(enabled)
        self.actionExportTraceAnimation.setEnabled(enabled)

        self.action1DPlot.setEnabled(False)
        self.action2DPlot.setEnabled(False)
        self.action3DPlot.setEnabled(False)

        for layer in layers:
            if isLayer1d(layer):
                self.action1DPlot.setEnabled(True)
            if isLayer2d(layer):
                self.action2DPlot.setEnabled(True)
            if isLayer3d(layer):
                self.action3DPlot.setEnabled(True)

