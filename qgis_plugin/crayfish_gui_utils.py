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



try:
  # for QGIS 2
  from qgis.gui import QgsCollapsibleGroupBox
except ImportError:
  # fallback to ordinary group box from Qt
  from PyQt4.QtGui import QGroupBox as QgsCollapsibleGroupBox



try:
  # this works in QGIS 2
  from qgis.gui import QgsMessageBar
  from qgis.utils import iface
  qgis_message_bar = iface.messageBar()

except ImportError:

  # compatibility layer for QGIS < 2.0 that does not support message bar
  from PyQt4.QtGui import QMessageBox

  class QgsMessageBar(object):
    INFO, WARNING, CRITICAL = range(3)
    msgbox = { INFO     : QMessageBox.information,
               WARNING  : QMessageBox.warning,
               CRITICAL : QMessageBox.critical }

    def pushMessage(self, title, message, level):
      self.msgbox[level](None, title, message)

  qgis_message_bar = QgsMessageBar()



def pixmap_colorRamp_default():
    from PyQt4.QtCore import QSize
    from PyQt4.QtGui import QPixmap, QPainter, QColor, QIcon

    s = QSize(50,16) #QgsColorRampComboBox.rampIconSize
    pix = QPixmap(s)
    p = QPainter(pix)
    for i in xrange(s.width()):
        h = int(240.0*i/(s.width()-1))
        p.setPen(QColor.fromHsv(h,255,255))
        p.drawLine(i,0,i,s.height()-1)
    p.end()
    return pix
