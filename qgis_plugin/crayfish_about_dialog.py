# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_about_dialog_widget import Ui_Dialog

class CrayfishAboutDialog(QDialog, Ui_Dialog):
    
    def __init__(self, iface):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.iface = iface
        
        pm = QPixmap( ":/plugins/crayfish/crayfish_128px.png" )
        self.crayfishIconLabel.setPixmap(pm)
        self.crayfishIconLabel.setMask( pm.mask() ) # required?
        
        pm = QPixmap( ":/plugins/crayfish/lutra_logo.png" )
        self.lutraLogoLabel.setPixmap(pm)
        self.lutraLogoLabel.setMask( pm.mask() ) # required?
        
        QObject.connect(self.aboutBrowser, SIGNAL("anchorClicked(QUrl)"), self.linkClicked)
        
        
    def __del__(self):
        QObject.disconnect(self.aboutBrowser, SIGNAL("anchorClicked(QUrl)"), self.linkClicked)
        
        
    def linkClicked(self, url):
        
        QDesktopServices.openUrl(url)

