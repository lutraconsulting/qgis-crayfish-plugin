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

import os
import datetime
import math

import qgis.core
import qgis.gui

from PyQt4.QtCore import QSize, QVariant, SIGNAL
from PyQt4.QtGui import QComboBox, QIcon, QPixmap, QColor, QColorDialog
from PyQt4 import uic


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


if not hasattr(qgis.gui, "QgsColorRampComboBox"):
  qgis.gui.QgsColorRampComboBox = QComboBox
  def _populate(self, style):
    if self.count() != 0:
      return
    self._style = style
    rampIconSize = QSize(50,16)
    self.setIconSize(rampIconSize)
    for rampName in style.colorRampNames():
      ramp = style.colorRamp(rampName)
      icon = qgis.core.QgsSymbolLayerV2Utils.colorRampPreviewIcon(ramp, rampIconSize)
      self.addItem(icon, rampName)
    #self.connect(self, SIGNAL("activated(int)"), self.colorRampChanged)
  qgis.gui.QgsColorRampComboBox.populate = _populate
  def _currentColorRamp(self):
    return self._style.colorRamp(self.currentText())
  qgis.gui.QgsColorRampComboBox.currentColorRamp = _currentColorRamp




def defaultColorRamp():
    props = {
      'color1': '0,0,255,255',
      'color2': '255,0,0,255',
      'stops' : '0.25;0,255,255,255:0.5;0,255,0,255:0.75;255,255,0,255'}
    return qgis.core.QgsVectorGradientColorRampV2.create(props)
    #stops = [ QgsGradientStop(0.25, Qt.yellow), QgsGradientStop(0.5, Qt.green) ]
    #return QgsVectorGradientColorRampV2(Qt.blue, Qt.red, False, stops)


def initColorRampComboBox(cbo):
    if hasattr(cbo, "setShowGradientOnly"):
      cbo.setShowGradientOnly(True)
    cbo.populate(qgis.core.QgsStyleV2.defaultStyle())
    iconSize = QSize(50,16)
    iconRamp = qgis.core.QgsSymbolLayerV2Utils.colorRampPreviewIcon(defaultColorRamp(), iconSize)
    cbo.setIconSize(iconSize)
    cbo.insertItem(0, iconRamp, "[default]")
    cbo.setCurrentIndex(0)


def name2ramp(rampName):
    return defaultColorRamp() if rampName == "[default]" else qgis.core.QgsStyleV2.defaultStyle().colorRamp(rampName)


def initColorButton(button):
  if not hasattr(button, "colorDialogTitle"):  # QGIS 1.x
    def _colorButtonClicked(self):
      clr = QColorDialog.getColor(self.color())
      if clr.isValid():
        self.setColor(clr)
        self.emit(SIGNAL("colorChanged(QColor)"), clr)
    button.colorButtonClicked = lambda: _colorButtonClicked(button)
    button.connect(button, SIGNAL("clicked()"), button.colorButtonClicked)


if not hasattr(qgis.core.QgsApplication, "getThemeIcon"):
  def _themeIcon(fileName):
    pix = QPixmap(qgis.core.QgsApplication.defaultThemePath()+"/"+fileName)
    if not pix.isNull():
        return QIcon(pix)
    # mapping from QGIS 2.0 icon file names to QGIS 1.x
    alternatives = { "/mActionOptions.svg" : "/mActionOptions.png",
      "/mActionFileSaveAs.svg" : "/mActionFileSaveAs.png", "/mActionFileOpen.svg" : "/mActionFileOpen.png",
      "/mActionSignPlus.png" : "/symbologyAdd.png", "/mActionSignMinus.png" : "/symbologyRemove.png" }
    if fileName in alternatives:
      return QIcon(qgis.core.QgsApplication.defaultThemePath()+"/"+alternatives[fileName])
    else:
      return QIcon()
  qgis.core.QgsApplication.getThemeIcon = staticmethod(_themeIcon)

if not hasattr(qgis.core.QgsVectorGradientColorRampV2, "count"):
  qgis.core.QgsVectorGradientColorRampV2.count = lambda self: len(self.stops())+2


#def qv2color(v):
#    return QColor(v) if isinstance(v, QVariant) else v

def qv2pyObj(v):
    return v.toPyObject() if isinstance(v, QVariant) else v

def qv2float(v):
    return v.toDouble()[0] if isinstance(v, QVariant) else v

def qv2int(v):
    return v.toInt()[0] if isinstance(v, QVariant) else v

def qv2bool(v):
    return v.toBool() if isinstance(v, QVariant) else v

def qv2string(v):
    return v.toString() if isinstance(v, QVariant) else v

def float_safe(txt):
    """ convert to float, return 0 if conversion is not possible """
    try:
        return float(txt)
    except ValueError:
        return 0.

def _hours_to_HHMMSS(hours):
    seconds = round(hours * 3600.0, 2)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%05.2f" % (h, m, s)

def time_to_string(time, ds=None):  # time is in hours
    #  TODO remove None
    # maybe would be worth to put this as direct replacement of output.time()...
    if ds:
        if ds.timeConfig["dt_use_absolute_time"]:
            res = ds.timeConfig["dt_reference_time"] + datetime.timedelta(hours=time)
            return res.strftime(ds.timeConfig["dt_datetime_format"])
        else:
            hours = time + ds.timeConfig["dt_offset_hours"]
            if ds.timeConfig["dt_time_format"] == "%H:%M:%S":
                return _hours_to_HHMMSS(hours)
            elif ds.timeConfig["dt_time_format"] == "%d %H:%M:%S":
                seconds = round(hours * 3600.0, 2)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                d, h = divmod(hours, 24)
                return "%02d %02d:%02d:%05.2f" % (d, h, m, s)
            elif ds.timeConfig["dt_time_format"] == "%d %H":
                d, h = divmod(hours, 24)
                return "%02d %05.3f" % (d, h)
            elif ds.timeConfig["dt_time_format"] == "%d":
                return "%06.3f" % (hours / 24.)
            elif ds.timeConfig["dt_time_format"] == "%H":
                return "%06.3f" % hours
            else:
                assert(False) # should never happen
    else:
        return _hours_to_HHMMSS(time)

def load_ui(name):
    ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'ui',
                          name + '.ui')
    return uic.loadUiType(ui_file)
