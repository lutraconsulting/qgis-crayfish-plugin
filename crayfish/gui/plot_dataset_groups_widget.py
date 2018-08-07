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


class DatasetGroupsMenu(QMenu):

    dataset_groups_changed = pyqtSignal(list)  # emits empty list when "current" is selected

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.layer = None
        self.action_current = None

    def populate_actions(self, layer):

        self.layer = layer
        self.clear()

        if layer is None or layer.dataProvider() is None:
            return

        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.triggered_action_current)
        self.addSeparator()

        layer.activeScalarDatasetChanged.connect(self.on_current_dataset_changed)

        for i in range(layer.dataProvider().datasetGroupCount()):
            a = self.addAction(layer.dataProvider().datasetGroupMetadata(i).name())
            a.group_index = i
            a.setCheckable(True)
            a.triggered.connect(self.triggered_action)

    def triggered_action(self):
        for a in self.actions():
          a.setChecked(a == self.sender())
        self.dataset_groups_changed.emit([self.sender().group_index])

    def triggered_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.dataset_groups_changed.emit([])

    def on_current_dataset_changed(self, index):
        if self.action_current.isChecked():
            self.dataset_groups_changed.emit([])  # re-emit changed signal

    def set_layer(self, layer):

        if layer is self.layer:
            return

        if self.layer is not None:
            self.layer.activeScalarDatasetChanged.disconnect(self.on_current_dataset_changed)

        self.populate_actions(layer)


class DatasetGroupsWidget(QToolButton):

    dataset_groups_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(QIcon(QPixmap(":/plugins/crayfish/images/icon_contours.png")))

        self.menu_datasets = DatasetGroupsMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_datasets)
        self.menu_datasets.dataset_groups_changed.connect(self.on_dataset_groups_changed)

        self.set_dataset_groups([])

    def on_dataset_groups_changed(self, lst):
        self.dataset_groups = lst
        if len(lst) == 0:
            self.setText("Group: [current]")
        elif len(lst) == 1:
            self.setText("Group: " + self.menu_datasets.layer.dataProvider().datasetGroupMetadata(lst[0]).name())
        self.dataset_groups_changed.emit(lst)

    def set_dataset_groups(self, lst):
        self.on_dataset_groups_changed(lst)

    def set_layer(self, layer):
        self.menu_datasets.set_layer(layer)
        self.set_dataset_groups([])
