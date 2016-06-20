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

uiDialog, qtBaseClass = load_ui('crayfish_export_raster_config_dialog')

class CrayfishExportRasterConfigDialog(qtBaseClass, uiDialog):
    def __init__(self, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)

        s = QSettings()
        self.spinResolution.setValue( float(s.value("crayfish/exportRasterResolution", 10)) )
        self.chkAddToCanvas.setChecked( int(s.value("crayfish/exportRasterAddToCanvas", 1)) )

    def saveSettings(self):
        s = QSettings()
        s.setValue("crayfish/exportRasterResolution", self.resolution())
        s.setValue("crayfish/exportRasterAddToCanvas", 1 if self.addToCanvas() else 0)

    def resolution(self):
        return self.spinResolution.value()
    def addToCanvas(self):
        return self.chkAddToCanvas.isChecked()
