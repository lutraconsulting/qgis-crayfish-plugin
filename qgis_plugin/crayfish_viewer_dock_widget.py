# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_viewer_dock_widget.ui'
#
# Created: Thu Oct 10 18:39:21 2013
#      by: PyQt4 UI code generator 4.10
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

class Ui_DockWidget(object):
    def setupUi(self, DockWidget):
        DockWidget.setObjectName(_fromUtf8("DockWidget"))
        DockWidget.resize(410, 535)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.listWidget = QtGui.QListWidget(self.dockWidgetContents)
        self.listWidget.setMinimumSize(QtCore.QSize(0, 55))
        self.listWidget.setMaximumSize(QtCore.QSize(16777215, 107))
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout_2.addWidget(self.listWidget)
        self.label_2 = QtGui.QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)
        self.listWidget_2 = QtGui.QListWidget(self.dockWidgetContents)
        self.listWidget_2.setMinimumSize(QtCore.QSize(0, 55))
        self.listWidget_2.setObjectName(_fromUtf8("listWidget_2"))
        self.verticalLayout_2.addWidget(self.listWidget_2)
        self.contoursGroupBox = QgsCollapsibleGroupBox(self.dockWidgetContents)
        self.contoursGroupBox.setCheckable(True)
        self.contoursGroupBox.setObjectName(_fromUtf8("contoursGroupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.contoursGroupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_3 = QtGui.QLabel(self.contoursGroupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_2.addWidget(self.label_3)
        self.contourTransparencySlider = QtGui.QSlider(self.contoursGroupBox)
        self.contourTransparencySlider.setMaximum(255)
        self.contourTransparencySlider.setPageStep(20)
        self.contourTransparencySlider.setOrientation(QtCore.Qt.Horizontal)
        self.contourTransparencySlider.setObjectName(_fromUtf8("contourTransparencySlider"))
        self.horizontalLayout_2.addWidget(self.contourTransparencySlider)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.contourCustomRangeCheckBox = QtGui.QCheckBox(self.contoursGroupBox)
        self.contourCustomRangeCheckBox.setObjectName(_fromUtf8("contourCustomRangeCheckBox"))
        self.verticalLayout.addWidget(self.contourCustomRangeCheckBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.contourMinLabel = QtGui.QLabel(self.contoursGroupBox)
        self.contourMinLabel.setObjectName(_fromUtf8("contourMinLabel"))
        self.horizontalLayout.addWidget(self.contourMinLabel)
        self.contourMinLineEdit = QtGui.QLineEdit(self.contoursGroupBox)
        self.contourMinLineEdit.setEnabled(False)
        self.contourMinLineEdit.setObjectName(_fromUtf8("contourMinLineEdit"))
        self.horizontalLayout.addWidget(self.contourMinLineEdit)
        self.contourMaxLabel = QtGui.QLabel(self.contoursGroupBox)
        self.contourMaxLabel.setObjectName(_fromUtf8("contourMaxLabel"))
        self.horizontalLayout.addWidget(self.contourMaxLabel)
        self.contourMaxLineEdit = QtGui.QLineEdit(self.contoursGroupBox)
        self.contourMaxLineEdit.setEnabled(False)
        self.contourMaxLineEdit.setObjectName(_fromUtf8("contourMaxLineEdit"))
        self.horizontalLayout.addWidget(self.contourMaxLineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.contoursGroupBox)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.displayVectorsCheckBox = QtGui.QCheckBox(self.dockWidgetContents)
        self.displayVectorsCheckBox.setObjectName(_fromUtf8("displayVectorsCheckBox"))
        self.gridLayout_3.addWidget(self.displayVectorsCheckBox, 1, 0, 1, 1)
        self.vectorOptionsPushButton = QtGui.QPushButton(self.dockWidgetContents)
        self.vectorOptionsPushButton.setEnabled(False)
        self.vectorOptionsPushButton.setObjectName(_fromUtf8("vectorOptionsPushButton"))
        self.gridLayout_3.addWidget(self.vectorOptionsPushButton, 1, 1, 1, 1)
        self.displayMeshCheckBox = QtGui.QCheckBox(self.dockWidgetContents)
        self.displayMeshCheckBox.setObjectName(_fromUtf8("displayMeshCheckBox"))
        self.gridLayout_3.addWidget(self.displayMeshCheckBox, 2, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_3)
        self.valueLabel = QtGui.QLabel(self.dockWidgetContents)
        self.valueLabel.setObjectName(_fromUtf8("valueLabel"))
        self.verticalLayout_2.addWidget(self.valueLabel)
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)
        QtCore.QObject.connect(self.displayVectorsCheckBox, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), DockWidget.displayVectorsButtonToggled)
        QtCore.QObject.connect(self.vectorOptionsPushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DockWidget.displayVectorPropsDialog)
        QtCore.QObject.connect(self.displayMeshCheckBox, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), DockWidget.displayMeshButtonToggled)
        QtCore.QMetaObject.connectSlotsByName(DockWidget)

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle(_translate("DockWidget", "Crayfish Viewer", None))
        self.label.setText(_translate("DockWidget", "Quantity", None))
        self.label_2.setText(_translate("DockWidget", "Output Time", None))
        self.contoursGroupBox.setTitle(_translate("DockWidget", "Display Contours", None))
        self.label_3.setText(_translate("DockWidget", "Transparency", None))
        self.contourCustomRangeCheckBox.setText(_translate("DockWidget", "Specifiy Color Scale", None))
        self.contourMinLabel.setText(_translate("DockWidget", "Min", None))
        self.contourMaxLabel.setText(_translate("DockWidget", "Max", None))
        self.displayVectorsCheckBox.setText(_translate("DockWidget", "Display Vectors", None))
        self.vectorOptionsPushButton.setText(_translate("DockWidget", "Vector Options", None))
        self.displayMeshCheckBox.setText(_translate("DockWidget", "Display Mesh", None))
        self.valueLabel.setText(_translate("DockWidget", "(0.000) 0.000", None))

from crayfish_gui_utils import QgsCollapsibleGroupBox
