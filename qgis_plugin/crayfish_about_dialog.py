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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_about_dialog_widget import Ui_Dialog
from version import crayfishPythonPluginVersion

class CrayfishAboutDialog(QDialog, Ui_Dialog):
    
    def __init__(self, iface):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.iface = iface
        
        self.aboutBrowser.setHtml( self.source() )
        
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

    def source(self):
        return """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd"><html><head><meta name="qrichtext" content="1" /><style type="text/css">p, li { white-space: pre-wrap; }</style></head><body style=" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;" bgcolor="#efe1bb"><p style=" margin-top:6px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; font-weight:600; color:#412824;">Crayfish Plugin</span></p>        <p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; color:#412824;">Version """ + crayfishPythonPluginVersion() + """</span></p>        <p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; color:#412824;">The Crayfish Plugin is a collection of tools for hydraulic modellers working with TUFLOW and other modelling packages. It aims to use QGIS as an efficient and effective pre and post-processor.</span></p>        <p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; color:#412824;">Check out the </span><a href="http://www.lutraconsulting.co.uk/resources/crayfish"><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; text-decoration: underline; color:#412824;">Crayfish resources page</span></a><span style=" font-family:'FreeSans,Geneva,Arial,sans-serif'; font-size:8pt; color:#412824;"> on our website for more information.</span></p>    </body></html>"""
