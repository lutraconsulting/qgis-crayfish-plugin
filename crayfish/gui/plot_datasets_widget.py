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
from qgis.core import QgsMeshDatasetIndex

from .utils import time_to_string

class DatasetsMenu(QMenu):

    datasets_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.layer = None
        self.set_dataset_group(None)
        self.dataset_group = -1

    def set_layer(self, layer):

        if layer is self.layer:
            return

        if self.layer is not None:
            self.layer.activeScalarDatasetChanged.disconnect(self.on_current_output_time_changed)

        if layer is not None:
            layer.activeScalarDatasetChanged.connect(self.on_current_output_time_changed)

        self.layer = layer
        self.set_dataset_group(layer.rendererSettings().activeScalarDataset().group() if layer is not None else -1)

    def set_dataset_group(self, dataset_group_index):
        self.dataset_group = dataset_group_index
        self.populate_actions(dataset_group_index)

    def populate_actions(self, dataset_group_index):

        # populate timesteps
        self.clear()

        if dataset_group_index is None or dataset_group_index < 0 or self.layer is None or self.layer.dataProvider() is None:
            return

        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.on_action_current)
        self.addSeparator()

        for i in range(self.layer.dataProvider().datasetCount(dataset_group_index)):
            meta = self.layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, i))
            a = self.addAction(time_to_string(meta.time()))
            a.dataset_index = i
            a.setCheckable(True)
            a.triggered.connect(self.on_action)

    def on_action(self):
        this_action = self.sender()

        if this_action.isChecked():
            self.action_current.setChecked(False)

        datasets = [a.dataset_index for a in self.actions() if a != self.action_current and a.isChecked()]
        if len(datasets) == 0:
            self.action_current.setChecked(True)

        self.datasets_changed.emit(datasets)

    def on_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.datasets_changed.emit([])

    def on_current_output_time_changed(self):
        if self.action_current.isChecked():
            self.datasets_changed.emit([])  # re-emit


class DatasetsWidget(QToolButton):

    datasets_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.menu_datasets = DatasetsMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_datasets)
        self.menu_datasets.datasets_changed.connect(self.on_datasets_changed)

        self.set_datasets([])

    def on_datasets_changed(self, lst):
        self.datasets = lst
        if len(lst) == 0:
            self.setText("Time: [current]")
        elif len(lst) == 1:
            meta = self.menu_datasets.layer.dataProvider().datasetMetadata(
                QgsMeshDatasetIndex(self.menu_datasets.dataset_group, lst[0])
            )
            self.setText("Time: " + time_to_string(meta.time()))
        else:
            self.setText("Time: [multiple]")

        self.datasets_changed.emit(lst)

    def set_dataset_group(self, ds):
        self.menu_datasets.set_dataset_group(ds)

    def set_datasets(self, lst):
        self.on_datasets_changed(lst)

    def set_layer(self, layer):
        self.menu_datasets.set_layer(layer)
        self.set_datasets([])
