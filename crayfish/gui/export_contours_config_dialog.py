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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .utils import load_ui

uiDialog, qtBaseClass = load_ui('crayfish_export_contours_dialog')

class CrayfishExportContoursConfigDialog(qtBaseClass, uiDialog):
    def __init__(self, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)

        s = QSettings()
        self.spinResolution.setValue( float(s.value("crayfish/exportContoursResolution", 10)) )
        self.spinContourInterval.setValue( float(s.value("crayfish/exportContoursInterval", 3)) )
        self.chkAddToCanvas.setChecked( int(s.value("crayfish/exportContoursAddToCanvas", 1)) )
        self.fixedLevelsRadio.setChecked( int(s.value("crayfish/exportContoursFixedLevels", 1)))
        self.useLinesRadio.setChecked( int(s.value("crayfish/exportContoursUseLines", 1)))


    def saveSettings(self):
        s = QSettings()
        s.setValue("crayfish/exportContoursResolution", self.resolution())
        s.setValue("crayfish/exportContoursInterval", self.interval())
        s.setValue("crayfish/exportContoursAddToCanvas", 1 if self.addToCanvas() else 0)
        s.setValue("crayfish/exportContoursFixedLevels", 1 if self.useFixedLevels() else 0)
        s.setValue("crayfish/exportContoursUseLines", 1 if self.useLines() else 0)

    def resolution(self):
        return self.spinResolution.value()

    def addToCanvas(self):
        return self.chkAddToCanvas.isChecked()

    def interval(self):
        return self.spinContourInterval.value()

    def useLines(self):
        return self.useLinesRadio.isChecked()

    def useAreas(self):
        return not self.useLines()

    def useFixedLevels(self):
        return self.fixedLevelsRadio.isChecked()
