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


from crayfish_animation_layout_item_props_ui import Ui_AnimationLayoutItemProps


class AnimationLayoutItemProps(QWidget, Ui_AnimationLayoutItemProps):

    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.btnFont.clicked.connect(self.onFontClicked)


    def setProps(self, props):

        self.prop_type = props['type']
        self.btnTextColor.setColor(props['text_color'])
        self.fnt = props['text_font']
        self.chkBackground.setChecked(props['bg'])
        self.btnBackgroundColor.setColor(props['bg_color'])

        # Label
        if props['type'] == 'title':
            self.editLabel.setText(props['label'])
        else:
            self.lblLabel.setVisible(False)
            self.editLabel.setVisible(False)

        # Time format
        if props['type'] == 'time':
            self.cboTimeFormat.setCurrentIndex(props['format'])
        else:
            self.lblTimeFormat.setVisible(False)
            self.cboTimeFormat.setVisible(False)

        # Position
        if props['type'] != 'title':
            self.cboPosition.setCurrentIndex(props['position'])
        else:
            self.cboPosition.setVisible(False)
            self.lblPosition.setVisible(False)


    def onFontClicked(self):
        fnt, ok = QFontDialog.getFont(self.fnt, self)
        if not ok:
            return
        self.fnt = fnt


    def props(self):
        p = { 'type' : self.prop_type, 'text_color' : self.btnTextColor.color(), 'text_font' : self.fnt }
        p['bg'] = self.chkBackground.isChecked()
        p['bg_color'] = self.btnBackgroundColor.color()
        if self.prop_type == 'title':
            p['label'] = self.editLabel.text()
        if self.prop_type == 'time':
            p['format'] = self.cboTimeFormat.currentIndex()
        if self.prop_type != 'title':
            p['position'] = self.cboPosition.currentIndex()
        return p
