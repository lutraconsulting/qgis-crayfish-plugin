# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'new_overlay_dialog_widget.ui'
#
# Created: Tue Jun 17 18:02:17 2014
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(397, 173)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/illuvis/illuvis_u_32w.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 2)
        self.layerLabel = QtGui.QLabel(Dialog)
        self.layerLabel.setObjectName(_fromUtf8("layerLabel"))
        self.gridLayout.addWidget(self.layerLabel, 2, 0, 1, 1)
        self.layerComboBox = QtGui.QComboBox(Dialog)
        self.layerComboBox.setEnabled(False)
        self.layerComboBox.setObjectName(_fromUtf8("layerComboBox"))
        self.layerComboBox.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.layerComboBox, 2, 1, 1, 1)
        self.columnForLabelsLabel = QtGui.QLabel(Dialog)
        self.columnForLabelsLabel.setObjectName(_fromUtf8("columnForLabelsLabel"))
        self.gridLayout.addWidget(self.columnForLabelsLabel, 3, 0, 1, 1)
        self.columnForLabelsComboBox = QtGui.QComboBox(Dialog)
        self.columnForLabelsComboBox.setEnabled(False)
        self.columnForLabelsComboBox.setObjectName(_fromUtf8("columnForLabelsComboBox"))
        self.columnForLabelsComboBox.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.columnForLabelsComboBox, 3, 1, 1, 1)
        self.overlayNameLabel = QtGui.QLabel(Dialog)
        self.overlayNameLabel.setObjectName(_fromUtf8("overlayNameLabel"))
        self.gridLayout.addWidget(self.overlayNameLabel, 4, 0, 1, 1)
        self.overlayNameLineEdit = QtGui.QLineEdit(Dialog)
        self.overlayNameLineEdit.setEnabled(False)
        self.overlayNameLineEdit.setObjectName(_fromUtf8("overlayNameLineEdit"))
        self.gridLayout.addWidget(self.overlayNameLineEdit, 4, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Help|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("helpRequested()")), Dialog.helpPressed)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.create)
        QtCore.QObject.connect(self.layerComboBox, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), Dialog.refreshColumns)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.overlayNameLineEdit, self.buttonBox)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "New Overlay", None))
        self.label_2.setText(_translate("Dialog", "Overlays are Point, Line or Polygon layers that are drawn in illuvis above flood data and can be used to highlight points of interest such as site boundaries or evacuation routes. Click Help for more details.", None))
        self.layerLabel.setText(_translate("Dialog", "Layer", None))
        self.layerComboBox.setItemText(0, _translate("Dialog", "-- Please Select --", None))
        self.columnForLabelsLabel.setText(_translate("Dialog", "Column for Labels", None))
        self.columnForLabelsComboBox.setItemText(0, _translate("Dialog", "-- None --", None))
        self.overlayNameLabel.setText(_translate("Dialog", "Overlay Name*", None))

import resources_rc
