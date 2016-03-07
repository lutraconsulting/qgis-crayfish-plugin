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

from .crayfish_gui_utils import timeToString


class OutputsMenu(QMenu):

    outputs_changed = pyqtSignal(list)

    def __init__(self, layer, parent=None):
        QMenu.__init__(self, parent)

        self.set_dataset(None)

        layer.currentOutputTimeChanged.connect(self.on_current_output_time_changed)

    def set_dataset(self, ds):

        # populate timesteps
        self.clear()
        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.on_action_current)
        self.addSeparator()

        if ds is None:
            return

        for output in ds.outputs():
            a = self.addAction(timeToString(output.time()))
            a.output = output
            a.setCheckable(True)
            a.triggered.connect(self.on_action)

    def on_action(self):
        for a in self.actions():
            a.setChecked(a == self.sender())
        self.outputs_changed.emit([self.sender().output])

    def on_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.outputs_changed.emit([])

    def on_current_output_time_changed(self):
        if self.action_current.isChecked():
            self.outputs_changed.emit([])   # re-emit


class OutputsWidget(QToolButton):

    outputs_changed = pyqtSignal(list)

    def __init__(self, layer, parent=None):
        QToolButton.__init__(self, parent)

        self.menu_outputs = OutputsMenu(layer)

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_outputs)
        self.menu_outputs.outputs_changed.connect(self.on_outputs_changed)

        self.set_outputs([])

    def on_outputs_changed(self, lst):
        self.outputs = lst
        if len(lst) == 0:
            self.setText("Time: [current]")
        elif len(lst) == 1:
            self.setText("Time: " + timeToString(lst[0].time()))

        self.outputs_changed.emit(lst)

    def set_dataset(self, ds):
        self.menu_outputs.set_dataset(ds)

    def set_outputs(self, lst):
        self.on_outputs_changed(lst)
