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

from qgis.core import QgsApplication, QgsStyleV2

from crayfish_colormap_dialog_ui import Ui_CrayfishColorMapDialog

from crayfishviewer import ColorMap

from crayfish_gui_utils import qv2string, qv2float, qv2int, initColorRampComboBox, name2ramp



class ColorMapModel(QAbstractTableModel):
    def __init__(self, cm):
        QAbstractTableModel.__init__(self)
        self.cm = cm

    def rowCount(self, parent):
        return len(self.cm.items) if not parent.isValid() else 0

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if index.row() < 0 or index.row() >= len(self.cm.items):
            return

        item = self.cm.items[index.row()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0: return item.value

        elif role == Qt.BackgroundRole:
            if index.column() == 1: return QBrush(QColor(item.color))

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return "Value"
            else: return "Color"

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0: f |= Qt.ItemIsEditable
        return f

    def setData(self, index, value, role):
        if role == Qt.EditRole and index.column() == 0:
            self.cm.item(index.row()).value = qv2float(value)
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index,index)
            self.ensureSorted()
            return True
        elif role == Qt.BackgroundRole and index.column() == 1:
            self.cm.item(index.row()).color = qv2int(value)
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index,index)
            return True
        return False

    def addItem(self):
        row = self.rowCount(QModelIndex())
        self.beginInsertRows(QModelIndex(), row, row)
        self.cm.addItem(ColorMap.Item(0, 0xff00ff00))
        self.endInsertRows()

        self.ensureSorted()

    def removeItem(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self.cm.removeItem(row)
        self.endRemoveRows()

    def ensureSorted(self):
        moved = False
        prev = self.cm.items[0].value
        for i in range(1,len(self.cm.items)):
            val = self.cm.items[i].value
            if val < prev:
              # find correct position
              for j in range(i):
                  if self.cm.items[j].value > val:
                      break
              # move the item
              self.beginMoveRows(QModelIndex(), i, i, QModelIndex(), j)
              self.cm.moveItem(i,j)
              self.endMoveRows()
              moved = True
            prev = self.cm.items[i].value

        if moved:
          self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self.index(0,0),self.index(len(self.cm.items),1))




class CrayfishColorMapDialog(QDialog, Ui_CrayfishColorMapDialog):
    def __init__(self, colormap, vMin, vMax, fnRedraw, parent=None):
        QDialog.__init__(self, parent)

        self.setupUi(self)

        self.buttonBox.hide()  # currently not used

        self.colormap = colormap
        self.vMin = vMin
        self.vMax = vMax
        self.fnRedraw = fnRedraw

        self.model = ColorMapModel(self.colormap)
        self.viewColorMap.setModel(self.model)

        initColorRampComboBox(self.cboColorRamp)

        self.btnAdd.setIcon(QgsApplication.getThemeIcon("/mActionSignPlus.png"))
        self.btnRemove.setIcon(QgsApplication.getThemeIcon("/mActionSignMinus.png"))
        self.btnLoad.setIcon(QgsApplication.getThemeIcon("/mActionFileOpen.svg"))
        self.btnSave.setIcon(QgsApplication.getThemeIcon("/mActionFileSaveAs.svg"))

        # make sure we accept only doubles for min/max values
        self.editMin.setValidator(QDoubleValidator(self.editMin))
        self.editMax.setValidator(QDoubleValidator(self.editMax))

        self.editMin.setText("%.3f" % vMin)
        self.editMax.setText("%.3f" % vMax)

        self.updateGUI()

        self.connect(self.btnAdd, SIGNAL("clicked()"), self.addItem)
        self.connect(self.btnRemove, SIGNAL("clicked()"), self.removeItem)
        self.connect(self.btnLoad, SIGNAL("clicked()"), self.loadColorMap)
        self.connect(self.btnSave, SIGNAL("clicked()"), self.saveColorMap)
        self.connect(self.btnClassify, SIGNAL("clicked()"), self.classify)
        self.connect(self.model, SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self.updatePreview)
        self.connect(self.model, SIGNAL("rowsInserted(QModelIndex,int,int)"), self.updatePreview)
        self.connect(self.model, SIGNAL("rowsRemoved(QModelIndex,int,int)"), self.updatePreview)
        #self.connect(self.model, SIGNAL("rowsMoved(QModelIndex,int,int,QModelIndex,int)"), self.updatePreview)
        self.connect(self.viewColorMap, SIGNAL("doubleClicked(QModelIndex)"), self.viewDoubleClicked)
        self.connect(self.radIntLinear, SIGNAL("clicked()"), self.setMethod)
        self.connect(self.radIntDiscrete, SIGNAL("clicked()"), self.setMethod)


    def updateGUI(self):
        """ update GUI from stored color map """
        if self.colormap.method == ColorMap.Discrete:
            self.radIntDiscrete.setChecked(True)
        else:
            self.radIntLinear.setChecked(True)

        self.updatePreview()


    def classify(self):

        ramp = name2ramp(self.cboColorRamp.currentText())
        if not ramp:
            return

        inv = self.chkInvert.isChecked()

        count = self.spinClasses.value()
        vmin = float(self.editMin.text())
        vmax = float(self.editMax.text())

        self.model.beginResetModel()
        self.colormap.clearItems()
        for i in range(count):
            x = float(i)/(count-1)
            v = vmin + (vmax-vmin)*x
            color = ramp.color(1-x if inv else x)
            self.colormap.addItem(ColorMap.Item(v, color.rgb()))
        self.model.endResetModel()

        self.updatePreview()

    def updatePreview(self):
        px = self.colormap.previewPixmap(QSize(self.lblPreview.size()), self.vMin, self.vMax)
        self.lblPreview.setPixmap(px)

        if self.fnRedraw:
          self.fnRedraw()


    def viewDoubleClicked(self, index):
        if index.column() != 1:
            return
        item = self.colormap.item(index.row())
        color = QColorDialog.getColor(QColor(item.color))
        if not color.isValid():
            return
        self.model.setData(index, color.rgb(), Qt.BackgroundRole)

    def addItem(self):
        self.model.addItem()

    def removeItem(self):
        lst = self.viewColorMap.selectionModel().selectedRows()
        if len(lst) == 1:
          self.model.removeItem(lst[0].row())

    def setMethod(self):
        self.colormap.method = ColorMap.Linear if self.radIntLinear.isChecked() else ColorMap.Discrete
        self.updatePreview()


    """
    # QGIS Generated Color Map Export File
    INTERPOLATION:INTERPOLATED
    152.402,215,25,28,255,152.402000
    177.554,253,174,97,255,177.553500
    202.705,255,255,191,255,202.705000
    227.857,171,221,164,255,227.856500
    253.008,43,131,186,255,253.008000
    """

    def loadColorMap(self):

        settings = QSettings()
        lastUsedDir = qv2string(settings.value("crayfishViewer/lastFolder"))
        fileName = QFileDialog.getOpenFileName(self, "Load color map", lastUsedDir, "Textfile (*.txt)")
        if not fileName:
            return

        self.model.beginResetModel
        self.colormap.clearItems()

        f = open(fileName, "r")
        for line in f.read().splitlines():
            if line.startswith("#"):
                continue
            elif line.startswith("INTERPOLATION:"):
                txt, method = line.split(":")
                self.colormap.method = ColorMap.Discrete if method == "DISCRETE" else ColorMap.Linear
            else:
                value, r,g,b,a, label = line.split(",")
                self.colormap.addItem(ColorMap.Item(float(value), qRgba(int(r),int(g),int(b),int(a))))

        self.model.endResetModel()

        self.updateGUI()


    def saveColorMap(self):

        settings = QSettings()
        lastUsedDir = qv2string(settings.value("crayfishViewer/lastFolder"))
        fileName = QFileDialog.getSaveFileName(self, "Save color map", lastUsedDir, "Textfile (*.txt)")
        if not fileName:
            return

        f = open(fileName, "w")
        f.write("# QGIS Generated Color Map Export File\n")
        f.write("INTERPOLATION:%s\n" % ("INTERPOLATED" if self.colormap.method == ColorMap.Linear else "DISCRETE"))
        for i in range(len(self.colormap.items)):
            item = self.colormap.items[i]
            c = QColor(item.color)
            f.write("%.3f,%d,%d,%d,%d,%.3f\n" % (item.value, c.red(), c.green(), c.blue(), c.alpha(), item.value))
        f.close()
