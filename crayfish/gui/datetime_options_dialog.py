# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2017 Lutra Consulting

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
from qgis.core import *

from .utils import load_ui, float_safe, time_to_string
import datetime

uiDialog, qtBaseClass = load_ui('crayfish_viewer_time_options_dialog_widget')


class CrayfishDatetimeOptionsDialog(qtBaseClass, uiDialog):
    def __init__(self, iface, time_settings, repopulate_time_control_combo, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)
        self.iface = iface
        self.ts = time_settings
        self.repopulate_time_control_combo = repopulate_time_control_combo

        # Populate the various widgets
        self.substractHoursEdit.setText(str(self.ts.substractHours))
        self.refDateTimeEdit.setDateTime(self.ts.refTime)

        self._populate_cb_widget("Use absolute time" if self.ts.useAbsoluteTime else "Use relative time", self.useTimeCB)
        self._populate_cb_widget(self.ts.dateTimeFormat, self.dateTimeFormatCB)
        self._populate_cb_widget(self.ts.timeFormat, self.timeFormatCB)

        self.enable_groups()

        # set validators so that user cannot type text into numeric line edits
        self.substractHoursEdit.setValidator(QDoubleValidator(self.substractHoursEdit))

        # Connect each of the widgets to the redraw function
        QObject.connect(self.substractHoursEdit, SIGNAL('textEdited(QString)'), self.input_focus_changed)
        QObject.connect(self.useTimeCB, SIGNAL('currentIndexChanged(int)'), self.input_focus_changed)
        QObject.connect(self.refDateTimeEdit, SIGNAL('dateTimeChanged(QDateTime)'), self.input_focus_changed)
        QObject.connect(self.timeFormatCB, SIGNAL('currentIndexChanged(int)'), self.input_focus_changed)
        QObject.connect(self.dateTimeFormatCB, SIGNAL('currentIndexChanged(int)'), self.input_focus_changed)

    def enable_groups(self):
        self.absoluteTimeGB.setEnabled(self.ts.useAbsoluteTime)
        self.relativeTimeGB.setEnabled(not self.ts.useAbsoluteTime)

    def _populate_cb_widget(self, val, w):
        idx = w.findText(val)
        if idx >= 0:
            w.setCurrentIndex(idx)
        else:
            w.addItem(val)
            w.setCurrentIndex(w.findText(val))

    def input_focus_changed(self, arg=None):
        self.save_settings()
        self.enable_groups()
        self.repopulate_time_control_combo(self.ts.dataSet())

    def save_settings(self):
        self.ts.useAbsoluteTime = (self.useTimeCB.currentText() == "Use absolute time")

        # abs time
        self.ts.refTime = self.refDateTimeEdit.dateTime().toPyDateTime()
        self.ts.dateTimeFormat = self.dateTimeFormatCB.currentText()

        # relative time
        try:
            self.ts.substractHours = float(self.substractHoursEdit.text())
        except ValueError:
            pass
        self.ts.timeFormat = self.timeFormatCB.currentText()

        # apply
        self.ts.apply_to_dataset()
