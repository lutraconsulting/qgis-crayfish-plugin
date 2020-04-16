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
from .gui.utils import mesh_layer_active_dataset_group_with_maximum_timesteps
from .processing import CrayfishProcessingProvider
from .resources import *

class CrayfishPlugin:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.plot_dock_widget = None
        self.plot_dock_3d_widget = None
        self.provider = CrayfishProcessingProvider()

    def initGui(self):
        # Add menu items
        self.mesh_menu = self.iface.mainWindow().findChild(QMenu, 'mMeshMenu')
        self.menu = self.mesh_menu.addMenu(QIcon(":/plugins/crayfish/images/crayfish.png"), "Crayfish")

        self.actionPlot = QAction(QIcon(":/plugins/crayfish/images/icon_plot.svg"), "Plot", self.iface.mainWindow())
        self.actionPlot.triggered.connect(self.toggle_plot)

        self.action3DPlot = QAction(QIcon(":/plugins/crayfish/images/icon_plot_3d.svg"), "3D Plot", self.iface.mainWindow())
        self.action3DPlot.triggered.connect(self.toggle_3d_plot)

        self.actionExportAnimation = QAction(QIcon(":/plugins/crayfish/images/icon_video.png"), "Export Animation ...", self.iface.mainWindow())
        self.actionExportAnimation.triggered.connect(self.exportAnimation)

        self.actionExportTraceAnimation=QAction(QIcon(":/plugins/crayfish/images/icon_video.png"),"Export Trace Animation ...", self.iface.mainWindow())
        self.actionExportTraceAnimation.triggered.connect(self.exportParticleTraceAnimation)

        self.menu.addAction(self.actionPlot)
        self.menu.addAction(self.action3DPlot)
        self.menu.addAction(self.actionExportAnimation)
        self.menu.addAction(self.actionExportTraceAnimation)

        # Register actions for context menu
        self.iface.addCustomActionForLayerType(self.actionPlot, '', QgsMapLayer.MeshLayer, True)
        self.iface.addCustomActionForLayerType(self.action3DPlot, '', QgsMapLayer.MeshLayer, True)
        self.iface.addCustomActionForLayerType(self.actionExportAnimation, '', QgsMapLayer.MeshLayer, True)
        self.iface.addCustomActionForLayerType(self.actionExportTraceAnimation, '', QgsMapLayer.MeshLayer, True)

        # Make connections
        self.iface.layerTreeView().currentLayerChanged.connect(self.active_layer_changed)

        # Create widget
        self.plot_dock_widget = QDockWidget("Crayfish Plot")
        self.plot_dock_widget.setObjectName("CrayfishPlotDock")
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_widget)
        w = CrayfishPlotWidget(self.plot_dock_widget)
        self.plot_dock_widget.setWidget(w)
        self.plot_dock_widget.hide()

        QgsApplication.processingRegistry().addProvider(self.provider)

    def active_layer_changed(self, layer):
        # only change layer when there is none selected
        if self.plot_dock_widget.widget().layer:
            return

        # only assign layer when active layer is a mesh layer
        if layer and layer.type() == QgsMapLayer.MeshLayer:
            self.plot_dock_widget.widget().set_layer(layer)

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


    def unload(self):
        # Remove menu item
        self.menu.removeAction(self.actionPlot)
        self.menu.removeAction(self.action3DPlot)
        self.menu.removeAction(self.actionExportAnimation)
        self.menu.removeAction(self.actionExportTraceAnimation)

        # Remove actions for context menu
        self.iface.removeCustomActionForLayerType(self.actionPlot)
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
