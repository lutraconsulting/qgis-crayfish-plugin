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

from .utils import load_ui

uiDialog, qtBaseClass = load_ui('crayfish_animation_layout_item_props')


class AnimationLayoutItemProps(qtBaseClass, uiDialog):

    def __init__(self, iface, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self)
        self.setupUi(self)

        self.btnFont.clicked.connect(self.onFontClicked)


    def setProps(self, props):

        self.prop_type = props['type']
        self.btnTextColor.setColor(props['text_color'])
        self.fnt = QFont(props['text_font'])  # need to make explicit copy
        self.chkBackground.setChecked(props['bg'])
        self.btnBackgroundColor.setColor(props['bg_color'])

        # Label
        if props['type'] == 'title':
            self.editLabel.setText(props['label'])
        else:
            self.lblLabel.setVisible(False)
            self.editLabel.setVisible(False)

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
        if self.prop_type != 'title':
            p['position'] = self.cboPosition.currentIndex()
        return p


    def storeDefaults(self, s):
        s.beginGroup("layout/"+self.prop_type)
        for k,v in self.props().items():
            if k == 'type': continue
            if k == 'text_font':
                s.setValue(k, v.toString())
            else:
                s.setValue(k, v)
        s.endGroup()


    def restoreDefaults(self, s):
        s.beginGroup("layout/"+ self.prop_type)
        for k in s.childKeys():
            if k == 'text_color':
                self.btnTextColor.setColor(s.value(k, type=QColor))
            elif k == 'text_font':
                self.fnt.fromString(s.value(k))
            elif k == 'bg':
                self.chkBackground.setChecked(s.value(k, type=bool))
            elif k == 'bg_color':
                self.btnBackgroundColor.setColor(s.value(k, type=QColor))
            elif k == 'label':
                self.editLabel.setText(s.value(k))
            elif k == 'position':
                self.cboPosition.setCurrentIndex(s.value(k, type=int))
        s.endGroup()
