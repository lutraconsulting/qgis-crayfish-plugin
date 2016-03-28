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
from qgis.core import *

from crayfish_ui_loader import load_ui
uiDialog, qtBaseClass = load_ui('crayfish_viewer_mesh_options_dialog_widget')

from crayfish_gui_utils import initColorButton

class CrayfishViewerMeshOptionsDialog(qtBaseClass, uiDialog):

    def __init__(self, layer, redrawFunction, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)

        self.layer = layer
        self.redrawFunction = redrawFunction

        self._init_color_buttons()
        self._load_from_config()
        self._connect_signals()

    def _init_color_buttons(self):
        initColorButton(self.borderColorButton)
        initColorButton(self.fillColorButton)
        self.borderColorButton.setColorDialogOptions(QColorDialog.ShowAlphaChannel)
        self.fillColorButton.setColorDialogOptions(QColorDialog.ShowAlphaChannel)

    def _connect_signals(self):
        self.borderColorButton.colorChanged.connect(self.setMeshBorderColor)
        self.fillColorButton.colorChanged.connect(self.setMeshFillColor)
        self.elementLabelCheckBox.toggled.connect(self.setMeshElementLabel)
        self.borderWidthSpinBox.valueChanged.connect(self.setMeshBorderWidth)
        self.fillGroupBox.toggled.connect(self.setMeshFillEnabled)

    def _load_from_config(self):
        c = self.layer.config["m_border_color"]
        self.borderColorButton.setColor(QColor(c[0],c[1],c[2],c[3]))

        c = self.layer.config["m_fill_color"]
        self.fillColorButton.setColor(QColor(c[0],c[1],c[2],c[3]))

        c = self.layer.config["m_label_elem"]
        self.elementLabelCheckBox.setChecked(c)

        c = self.layer.config["m_border_width"]
        self.borderWidthSpinBox.setValue(c)

        c = self.layer.config["m_fill_enabled"]
        self.fillGroupBox.setChecked(c)

    def setMeshBorderColor(self, clr):
        self.layer.config["m_border_color"] = (clr.red(),clr.green(),clr.blue(),clr.alpha())
        self.redrawFunction()

    def setMeshFillColor(self, clr):
        self.layer.config["m_fill_color"] = (clr.red(),clr.green(),clr.blue(),clr.alpha())
        self.redrawFunction()

    def setMeshBorderWidth(self, clr):
        self.layer.config["m_border_width"] = clr
        self.redrawFunction()

    def setMeshElementLabel(self, clr):
        self.layer.config["m_label_elem"] = clr
        self.redrawFunction()

    def setMeshFillEnabled(self, clr):
        self.layer.config["m_fill_enabled"] = clr
        self.redrawFunction()
