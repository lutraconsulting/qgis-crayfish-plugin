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

from qgis.core import QgsMapLayer, QgsProject, QgsMeshLayer


class CrayfishLayerMenu(QMenu):

    picked_layer = pyqtSignal(QgsMapLayer)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().layersWillBeRemoved.connect(self.layers_will_be_removed)

        self.layers_added( QgsProject.instance().mapLayers().values() )

    def layers_added(self, lst):
        for layer in lst:
            if not isinstance(layer, QgsMeshLayer):
                continue
            a = self.addAction(layer.name())
            a.layer_id = layer.id()
            a.triggered.connect(self.triggered_action)

    def layers_will_be_removed(self, lst):
        for action in self.actions():
            if action.layer_id in lst:
                self.removeAction(action)

    def triggered_action(self):
        self.picked_layer.emit( QgsProject.instance().mapLayer(self.sender().layer_id) )


class CrayfishLayerWidget(QToolButton):

    layer_changed = pyqtSignal(QgsMapLayer)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.layer = None

        self.menu_layers = CrayfishLayerMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_layers)
        self.menu_layers.picked_layer.connect(self.on_picked_layer)

        QgsProject.instance().layersWillBeRemoved.connect(self.layers_will_be_removed)
        self.set_layer(None)

    def set_layer(self, layer):
        self.on_picked_layer(layer)

    def on_picked_layer(self, layer):
        layer_name = layer.name() if layer is not None else "(none)"
        self.setText("Layer: " + layer_name)
        self.layer = layer
        self.layer_changed.emit(layer)

    def layers_will_be_removed(self, lst):
        if self.layer and self.layer.id() in lst:
            self.set_layer(None)
