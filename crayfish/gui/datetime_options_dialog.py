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

from .utils import load_ui, float_safe
import datetime

uiDialog, qtBaseClass = load_ui('crayfish_viewer_time_options_dialog_widget')


class CrayfishDatetimeOptionsDialog(qtBaseClass, uiDialog):
    def __init__(self, iface, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)
        self.iface = iface

    def format_time(self, hours):
        substract_hours = float_safe(self.substractHoursEdit.text())
        hours = hours - substract_hours

        if self.absoluteTimeGB.isChecked():
            reftime = self.refDateTimeEdit.dateTime()
            res = reftime + datetime.timedelta(hours=hours)
            fstring = self.timeFormatCB().currentText()
            return res.strftime(fstring)
        else:
            seconds = round(hours * 3600.0, 2)
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return "%02d:%02d:%05.2f" % (h, m, s)
