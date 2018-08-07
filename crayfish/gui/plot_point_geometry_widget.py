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

import math

from qgis.core import *
from qgis.gui import *
from qgis.utils import iface

from .plot_map_layer_widget import MapLayersWidget


class PickGeometryTool(QgsMapTool):

    picked = pyqtSignal(QgsPointXY, bool, bool)   # point, whether clicked or just moving, whether clicked with Ctrl

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)

    def canvasMoveEvent(self, e):
        #if e.button() == Qt.LeftButton:
        self.picked.emit(e.mapPoint(), False, False)

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.picked.emit(e.mapPoint(), True, e.modifiers() & Qt.ControlModifier)

    def canvasReleaseEvent(self, e):
        pass



class PointGeometryPickerWidget(QWidget):

    geometries_changed = pyqtSignal()

    PICK_NO, PICK_MAP, PICK_LAYER = range(3)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.pick_mode = self.PICK_NO
        self.pick_layer = None
        self.geometries = []
        self.temp_geometry_index = -1

        self.btn_picker = QToolButton()
        self.btn_picker.setText("From map")
        self.btn_picker.setCheckable(True)
        self.btn_picker.clicked.connect(self.picker_clicked)

        self.btn_layer = MapLayersWidget(QgsWkbTypes.Point)
        self.btn_layer.picked_layer.connect(self.on_picked_layer)

        self.tool = PickGeometryTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)
        self.tool.setButton(self.btn_picker)

        layout = QHBoxLayout()
        layout.addWidget(self.btn_picker)
        layout.addWidget(self.btn_layer)

        self.setLayout(layout)

    def clear_geometries(self):
        self.geometries = []
        self.temp_geometry_index = -1
        self.geometries_changed.emit()

    def picker_clicked(self):

        was_active = (self.pick_mode == self.PICK_MAP)
        self.stop_picking()

        if not was_active:
            self.start_picking_map()

    def start_picking_map(self):
        self.pick_mode = self.PICK_MAP
        iface.mapCanvas().setMapTool(self.tool)
        self.clear_geometries()

    def stop_picking(self):
        if self.pick_mode == self.PICK_MAP:
            iface.mapCanvas().unsetMapTool(self.tool)
        elif self.pick_mode == self.PICK_LAYER:
            self.pick_layer.selectionChanged.disconnect(self.on_pick_selection_changed)
            self.pick_layer = None
        self.pick_mode = self.PICK_NO

    def on_picked(self, pt, clicked, with_ctrl):

        geom = QgsGeometry.fromPointXY(pt)
        if clicked:
            if self.temp_geometry_index == -1:
                self.geometries.append(geom)
            else:
                self.geometries[self.temp_geometry_index] = geom
                self.temp_geometry_index = -1
        else:   # just doing mouse move
            if self.temp_geometry_index == -1:
                self.temp_geometry_index = len(self.geometries)
                self.geometries.append(geom)
            else:
                self.geometries[self.temp_geometry_index] = geom

        self.geometries_changed.emit()

        if clicked and not with_ctrl:  # no more updates
            self.stop_picking()

    def on_picked_layer(self, layer_id):

        self.stop_picking()

        self.pick_layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        if not self.pick_layer:
            return

        self.pick_mode = self.PICK_LAYER
        self.pick_layer.selectionChanged.connect(self.on_pick_selection_changed)

        self.on_pick_selection_changed()

    def on_pick_selection_changed(self):

        self.geometries = [QgsGeometry(f.geometry()) for f in self.pick_layer.selectedFeatures()]
        self.temp_geometry_index = -1
        self.geometries_changed.emit()