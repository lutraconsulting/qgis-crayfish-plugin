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


class CrayfishPlugin:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.plot_dock_widget = None

    def initGui(self):
        # Add menu item
        self.menu = self.iface.pluginMenu().addMenu(QIcon(":/plugins/crayfish/images/crayfish.png"), "Crayfish")
        self.actionPlot = QAction(QgsApplication.getThemeIcon("/histogram.png"), "Plot", self.iface.mainWindow())
        self.menu.addAction(self.actionPlot)
        self.actionPlot.triggered.connect(self.toggle_plot)

        # Make connections
        self.iface.layerTreeView().currentLayerChanged.connect(self.active_layer_changed)

        # Create widget
        self.plot_dock_widget = QDockWidget("Crayfish Plot")
        self.plot_dock_widget.setObjectName("CrayfishPlotDock")
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_widget)
        w = CrayfishPlotWidget(self.plot_dock_widget)
        self.plot_dock_widget.setWidget(w)
        self.plot_dock_widget.hide()

    def active_layer_changed(self, layer):
        # only change layer when there is none selected
        if self.plot_dock_widget.widget().layer:
            return

        # only assign layer when active layer is a mesh layer
        if layer and layer.type() == QgsMapLayer.MeshLayer:
            self.plot_dock_widget.widget().set_layer(layer)

    def toggle_plot(self):
        self.plot_dock_widget.setVisible(not self.plot_dock_widget.isVisible())

    def unload(self):
        # Remove connections
        self.iface.layerTreeView().currentLayerChanged.disconnect(self.active_layer_changed)

        # Remove widgets
        self.layer = None
        self.plot_dock_widget.close()
        self.iface.removeDockWidget(self.plot_dock_widget)


