# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_viewer_dock_widget.ui'
#
# Created: Wed Oct 10 22:54:06 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DockWidget(object):
    def setupUi(self, DockWidget):
        DockWidget.setObjectName(_fromUtf8("DockWidget"))
        DockWidget.resize(460, 456)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.gridLayout_2 = QtGui.QGridLayout(self.dockWidgetContents)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.listWidget = QtGui.QListWidget(self.dockWidgetContents)
        self.listWidget.setMinimumSize(QtCore.QSize(0, 55))
        self.listWidget.setMaximumSize(QtCore.QSize(16777215, 107))
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout.addWidget(self.listWidget)
        self.label_2 = QtGui.QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.listWidget_2 = QtGui.QListWidget(self.dockWidgetContents)
        self.listWidget_2.setMinimumSize(QtCore.QSize(0, 55))
        self.listWidget_2.setObjectName(_fromUtf8("listWidget_2"))
        self.verticalLayout.addWidget(self.listWidget_2)
        self.groupBox = QtGui.QGroupBox(self.dockWidgetContents)
        self.groupBox.setEnabled(True)
        self.groupBox.setCheckable(True)
        self.groupBox.setChecked(False)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.minLabel = QtGui.QLabel(self.groupBox)
        self.minLabel.setObjectName(_fromUtf8("minLabel"))
        self.horizontalLayout.addWidget(self.minLabel)
        self.minLineEdit = QtGui.QLineEdit(self.groupBox)
        self.minLineEdit.setEnabled(False)
        self.minLineEdit.setObjectName(_fromUtf8("minLineEdit"))
        self.horizontalLayout.addWidget(self.minLineEdit)
        self.maxLabel = QtGui.QLabel(self.groupBox)
        self.maxLabel.setObjectName(_fromUtf8("maxLabel"))
        self.horizontalLayout.addWidget(self.maxLabel)
        self.maxLineEdit = QtGui.QLineEdit(self.groupBox)
        self.maxLineEdit.setEnabled(False)
        self.maxLineEdit.setObjectName(_fromUtf8("maxLineEdit"))
        self.horizontalLayout.addWidget(self.maxLineEdit)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.contourOptionsPushButton = QtGui.QPushButton(self.dockWidgetContents)
        self.contourOptionsPushButton.setEnabled(False)
        self.contourOptionsPushButton.setObjectName(_fromUtf8("contourOptionsPushButton"))
        self.gridLayout_3.addWidget(self.contourOptionsPushButton, 1, 0, 1, 1)
        self.vectorOptionsPushButton = QtGui.QPushButton(self.dockWidgetContents)
        self.vectorOptionsPushButton.setEnabled(False)
        self.vectorOptionsPushButton.setObjectName(_fromUtf8("vectorOptionsPushButton"))
        self.gridLayout_3.addWidget(self.vectorOptionsPushButton, 1, 1, 1, 1)
        self.displayContoursCheckBox = QtGui.QCheckBox(self.dockWidgetContents)
        self.displayContoursCheckBox.setChecked(True)
        self.displayContoursCheckBox.setObjectName(_fromUtf8("displayContoursCheckBox"))
        self.gridLayout_3.addWidget(self.displayContoursCheckBox, 0, 0, 1, 1)
        self.displayVectorsCheckBox = QtGui.QCheckBox(self.dockWidgetContents)
        self.displayVectorsCheckBox.setObjectName(_fromUtf8("displayVectorsCheckBox"))
        self.gridLayout_3.addWidget(self.displayVectorsCheckBox, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_3)
        self.valueLabel = QtGui.QLabel(self.dockWidgetContents)
        self.valueLabel.setObjectName(_fromUtf8("valueLabel"))
        self.verticalLayout.addWidget(self.valueLabel)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)
        QtCore.QObject.connect(self.displayContoursCheckBox, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), DockWidget.displayContoursButtonToggled)
        QtCore.QObject.connect(self.displayVectorsCheckBox, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), DockWidget.displayVectorsButtonToggled)
        QtCore.QObject.connect(self.vectorOptionsPushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), DockWidget.displayVectorPropsDialog)
        QtCore.QMetaObject.connectSlotsByName(DockWidget)

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle(QtGui.QApplication.translate("DockWidget", "Crayfish Viewer", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DockWidget", "Quantity", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DockWidget", "Output Time", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("DockWidget", "Specify Colour Scale", None, QtGui.QApplication.UnicodeUTF8))
        self.minLabel.setText(QtGui.QApplication.translate("DockWidget", "Min", None, QtGui.QApplication.UnicodeUTF8))
        self.maxLabel.setText(QtGui.QApplication.translate("DockWidget", "Max", None, QtGui.QApplication.UnicodeUTF8))
        self.contourOptionsPushButton.setText(QtGui.QApplication.translate("DockWidget", "Contour Options", None, QtGui.QApplication.UnicodeUTF8))
        self.vectorOptionsPushButton.setText(QtGui.QApplication.translate("DockWidget", "Vector Options", None, QtGui.QApplication.UnicodeUTF8))
        self.displayContoursCheckBox.setText(QtGui.QApplication.translate("DockWidget", "Display Contours", None, QtGui.QApplication.UnicodeUTF8))
        self.displayVectorsCheckBox.setText(QtGui.QApplication.translate("DockWidget", "Display Vectors", None, QtGui.QApplication.UnicodeUTF8))
        self.valueLabel.setText(QtGui.QApplication.translate("DockWidget", "(0.000) 0.000", None, QtGui.QApplication.UnicodeUTF8))

