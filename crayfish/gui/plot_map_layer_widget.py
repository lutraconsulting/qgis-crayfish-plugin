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



def geom2icon(geom_type):
    if geom_type == QgsWkbTypes.Point:
        return QgsLayerItem.iconPoint()
    elif geom_type == QgsWkbTypes.Polygon:
        return QgsLayerItem.iconPolygon()
    elif geom_type == QgsWkbTypes.LineString:
        return QgsLayerItem.iconLine()
    else:
        return QIcon()


class MapLayerMenu(QMenu):

    picked_layer = pyqtSignal(unicode)

    def __init__(self, geom_type, parent=None):
        QMenu.__init__(self, parent)

        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().layersWillBeRemoved.connect(self.layers_will_be_removed)

        self.geom_type = geom_type
        self.layers_added( QgsProject.instance().mapLayers().values() )

    def layers_added(self, lst):
        for layer in lst:
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() != self.geom_type:
                continue
            a = self.addAction(geom2icon(layer.geometryType()), layer.name())
            a.layer_id = layer.id()
            a.triggered.connect(self.triggered_action)

    def layers_will_be_removed(self, lst):
        for action in self.actions():
            if action.layer_id in lst:
                self.removeAction(action)

    def triggered_action(self):
        self.picked_layer.emit(self.sender().layer_id)



class MapLayersWidget(QToolButton):

    picked_layer = pyqtSignal(unicode)

    def __init__(self, geom_type, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(geom2icon(geom_type))

        self.menu_layers = MapLayerMenu(geom_type)

        self.setText("From layer")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_layers)
        self.menu_layers.picked_layer.connect(self.picked_layer)

