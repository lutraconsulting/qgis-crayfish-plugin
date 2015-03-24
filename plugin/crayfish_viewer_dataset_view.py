# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2015 Lutra Consulting

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

import sip
sip.setapi('QVariant', 2)

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class DataSetTreeNode(object):
    def __init__(self, ds_index, ds_name, ds_type, parentItem):
        self.ds_index = ds_index
        self.ds_name = ds_name
        self.ds_type = ds_type
        self.parentItem = parentItem
        self.childItems = []

    def appendChild(self, item):  self.childItems.append(item)
    def child(self, row):         return self.childItems[row]
    def childCount(self):         return len(self.childItems)
    def columnCount(self):        return 1
    def parent(self):             return self.parentItem
    def row(self):  return self.parentItem.childItems.index(self) if self.parentItem else 0


class DataSetModel(QAbstractItemModel):
    def __init__(self, datasets, parent=None) :
        QAbstractItemModel.__init__(self, parent)
        self.rootItem = DataSetTreeNode(None, None, None, None)
        self.setMesh(datasets)

    def setMesh(self, datasets):
        self.c_active = None
        self.v_active = None
        self.name2item = {}
        self.dsindex2item = {}
        for i,d in enumerate(datasets):
            ds_name, ds_type = d
            lst = ds_name.split('/')
            if len(lst) == 1:  # top-level item
              item = DataSetTreeNode(i, ds_name, ds_type, self.rootItem)
              self.rootItem.appendChild(item)
              self.name2item[ds_name] = item
              self.dsindex2item[i] = item

            elif len(lst) == 2: # child item
              ds_parent_name, ds_name = lst
              if ds_parent_name in self.name2item:
                itemParentDs = self.name2item[ds_parent_name]
                item = DataSetTreeNode(i, ds_name, ds_type, itemParentDs)
                itemParentDs.appendChild(item)
                self.dsindex2item[i] = item
              else:
                print "ignoring invalid child dataset"
            else:
              print "ignoring too deep child dataset"

    def activeContourIndex(self):
        return self.c_active.ds_index if self.c_active is not None else -1

    def setActiveContourIndex(self, index):
        self.setActive("contour", index)

    def activeVectorIndex(self):
        return self.v_active.ds_index if self.v_active is not None else -1

    def setActiveVectorIndex(self, index):
        self.setActive("vector", index)

    def setActive(self, name, index):
        item = self.dsindex2item[index] if index in self.dsindex2item else None
        if name == "vector":
            old_idx = self.item2index(self.v_active)
            self.v_active = item
        elif name == "contour":
            old_idx = self.item2index(self.c_active)
            self.c_active = item

        if old_idx is not None:
            self.dataChanged.emit(old_idx,old_idx)
        new_idx = self.item2index(item)
        if new_idx is not None:
            self.dataChanged.emit(new_idx,new_idx)

    def item2index(self, item):
        if item is None:
            return None
        elif item.parentItem is None:
            return QModelIndex()
        else:
            return self.index(item.row(), 0, self.item2index(item.parentItem))

    def index2item(self, index):
        if index is None or not index.isValid():
          return self.rootItem
        else:
          return index.internalPointer()

    def datasetIndex2item(self, ds_index):
        return self.dsindex2item[ds_index] if ds_index in self.dsindex2item else None

    def rowCount(self, parent=None):
        if parent and parent.column() > 0:
          return 0
        return self.index2item(parent).childCount()

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return

        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.ds_name
        if role == Qt.UserRole:
            return item.ds_type
        if role == Qt.UserRole+1:
            return item == self.c_active
        if role == Qt.UserRole+2:
            return item == self.v_active

    def index(self, row, column, parent=None):
        if parent is None: parent = QModelIndex()
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if not childItem:
            return QModelIndex()

        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)


POS_V, POS_C = 1, 2   # identifiers of positions of icons in the delegate

class DataSetItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)
        self.pix_c  = QPixmap(":/plugins/crayfish/icon_contours.png")
        self.pix_c0 = QIcon(self.pix_c).pixmap(self.pix_c.width(),self.pix_c.height(), QIcon.Disabled)
        self.pix_v = QPixmap(":/plugins/crayfish/icon_vectors.png")
        self.pix_v0 = QPixmap(":/plugins/crayfish/icon_vectors_disabled.png")
        #self.pix_v0 = QIcon(self.pix_v).pixmap(self.pix_v.width(),self.pix_v.height(), QIcon.Disabled)

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)

        if index.data(Qt.UserRole) == 2:  # also Vector
            av = index.data(Qt.UserRole+2)
            painter.drawPixmap(self.iconRect(option.rect, POS_V), self.pix_v if av else self.pix_v0)
        ac = index.data(Qt.UserRole+1)
        painter.drawPixmap(self.iconRect(option.rect, POS_C), self.pix_c if ac else self.pix_c0)

    def iconRect(self, rect, i):
        """ icon rect for given item rect. i is either POS_C or POS_V """
        iw, ih =  self.pix_c.width(), self.pix_c.height()
        margin = (rect.height()-ih)/2
        return QRect(rect.right() - i*(iw + margin), rect.top() + margin, iw, ih)



class DataSetView(QTreeView):

    contourClicked = pyqtSignal(int)
    vectorClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        QTreeView.__init__(self, parent)

        self.setItemDelegate(DataSetItemDelegate())
        #self.setRootIsDecorated(False)
        self.setHeaderHidden(True)

        self.customActions = []

    def setCustomActions(self, actions):
        self.customActions = actions

    def mousePressEvent(self, event):
        processed = False
        idx = self.indexAt(event.pos())
        if idx.isValid():
          vr = self.visualRect(idx)
          if self.itemDelegate().iconRect(vr, POS_V).contains(event.pos()):
            if idx.data(Qt.UserRole) == 2: # has vector data?
              self.vectorClicked.emit(self.model().index2item(idx).ds_index)
              processed = True
          elif self.itemDelegate().iconRect(vr, POS_C).contains(event.pos()):
            self.contourClicked.emit(self.model().index2item(idx).ds_index)
            processed = True

        # only if the user did not click one of the icons do usual handling
        if not processed:
            QTreeView.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        if len(self.customActions) == 0:
            return
        event.accept()
        m = QMenu()
        for a in self.customActions:
            m.addAction(a)
        m.exec_(self.mapToGlobal(event.pos()))

def test_main():
    datasets = [("Bed Elevation", 0), ("Depth", 1), ("Depth/Max", 1), ("Velocity", 2), ("Unit Flow", 2)]
    v = DataSetView()
    v.setModel(DataSetModel(datasets))
    btn = QToolButton()
    btn.setCheckable(True)
    btn.setChecked(True)
    w = QWidget()
    l = QVBoxLayout()
    l.addWidget(btn)
    l.addWidget(v)
    w.setLayout(l)
    w.show()
    v.setCurrentIndex(v.model().index(0,0))
    return w

if __name__ == '__main__':
    a = QApplication([])
    w = test_main()
    a.exec_()
    del w
