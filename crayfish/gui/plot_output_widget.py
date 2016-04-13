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

from .utils import time_to_string


class OutputsMenu(QMenu):

    outputs_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.layer = None
        self.set_dataset(None)

    def set_layer(self, layer):

        if layer is self.layer:
            return

        if self.layer is not None:
            self.layer.currentOutputTimeChanged.disconnect(self.on_current_output_time_changed)

        if layer is not None:
            layer.currentOutputTimeChanged.connect(self.on_current_output_time_changed)

        self.populate_actions(layer.currentDataSet() if layer is not None else None)
        self.layer = layer

    def set_dataset(self, ds):
        self.populate_actions(ds)

    def populate_actions(self, ds):

        # populate timesteps
        self.clear()

        if ds is None:
            return

        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.on_action_current)
        self.addSeparator()

        for output in ds.outputs():
            a = self.addAction(time_to_string(output.time()))
            a.output = output
            a.setCheckable(True)
            a.triggered.connect(self.on_action)

    def on_action(self):
        this_action = self.sender()

        if this_action.isChecked():
            self.action_current.setChecked(False)

        outputs = [ a.output for a in self.actions() if a != self.action_current and a.isChecked() ]
        if len(outputs) == 0:
            self.action_current.setChecked(True)

        self.outputs_changed.emit(outputs)

    def on_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.outputs_changed.emit([])

    def on_current_output_time_changed(self):
        if self.action_current.isChecked():
            self.outputs_changed.emit([])   # re-emit


class OutputsWidget(QToolButton):

    outputs_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.menu_outputs = OutputsMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_outputs)
        self.menu_outputs.outputs_changed.connect(self.on_outputs_changed)

        self.set_outputs([])

    def on_outputs_changed(self, lst):
        self.outputs = lst
        if len(lst) == 0:
            self.setText("Time: [current]")
        elif len(lst) == 1:
            self.setText("Time: " + time_to_string(lst[0].time()))
        else:
            self.setText("Time: [multiple]")

        self.outputs_changed.emit(lst)

    def set_dataset(self, ds):
        self.menu_outputs.set_dataset(ds)

    def set_outputs(self, lst):
        self.on_outputs_changed(lst)

    def set_layer(self, layer):
        self.menu_outputs.set_layer(layer)
        self.set_outputs([])
