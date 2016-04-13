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


class DatasetsMenu(QMenu):

    datasets_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.layer = None
        self.action_current = None


    def populate_actions(self, layer):

        self.layer = layer
        self.clear()

        if layer is None:
            return

        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.triggered_action_current)
        self.addSeparator()

        layer.currentDataSetChanged.connect(self.on_current_dataset_changed)

        for ds in layer.mesh.datasets():
            a = self.addAction(ds.name())
            a.ds = ds
            a.setCheckable(True)
            a.triggered.connect(self.triggered_action)

    def triggered_action(self):
        for a in self.actions():
          a.setChecked(a == self.sender())
        self.datasets_changed.emit([self.sender().ds])

    def triggered_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.datasets_changed.emit([])

    def on_current_dataset_changed(self):
        if self.action_current.isChecked():
            self.datasets_changed.emit([])  # re-emit changed signal

    def set_layer(self, layer):

        if layer is self.layer:
            return

        if self.layer is not None:
            self.layer.currentDataSetChanged.disconnect(self.on_current_dataset_changed)

        self.populate_actions(layer)


class DatasetsWidget(QToolButton):

    datasets_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(QIcon(QPixmap(":/plugins/crayfish/icon_contours.png")))

        self.menu_datasets = DatasetsMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_datasets)
        self.menu_datasets.datasets_changed.connect(self.on_datasets_changed)

        self.set_datasets([])

    def on_datasets_changed(self, lst):
        self.datasets = lst
        if len(lst) == 0:
            self.setText("Dataset: [current]")
        elif len(lst) == 1:
            self.setText("Dataset: " + lst[0].name())
        self.datasets_changed.emit(lst)

    def set_datasets(self, lst):
        self.on_datasets_changed(lst)

    def set_layer(self, layer):
        self.menu_datasets.set_layer(layer)
        self.set_datasets([])
