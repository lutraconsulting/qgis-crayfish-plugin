# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_viewer_plugin_layer_props_dialog.ui'
#
# Created: Tue Oct  8 19:34:29 2013
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

class Ui_CrayfishViewerPluginLayerPropsDialog(object):
    def setupUi(self, CrayfishViewerPluginLayerPropsDialog):
        CrayfishViewerPluginLayerPropsDialog.setObjectName(_fromUtf8("CrayfishViewerPluginLayerPropsDialog"))
        CrayfishViewerPluginLayerPropsDialog.resize(514, 385)
        self.verticalLayout_2 = QtGui.QVBoxLayout(CrayfishViewerPluginLayerPropsDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.groupBox = QtGui.QGroupBox(CrayfishViewerPluginLayerPropsDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.editCRS = QtGui.QLineEdit(self.groupBox)
        self.editCRS.setReadOnly(True)
        self.editCRS.setObjectName(_fromUtf8("editCRS"))
        self.horizontalLayout.addWidget(self.editCRS)
        self.btnSpecifyCRS = QtGui.QPushButton(self.groupBox)
        self.btnSpecifyCRS.setObjectName(_fromUtf8("btnSpecifyCRS"))
        self.horizontalLayout.addWidget(self.btnSpecifyCRS)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(CrayfishViewerPluginLayerPropsDialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.editMetadata = QtGui.QTextEdit(self.groupBox_2)
        self.editMetadata.setObjectName(_fromUtf8("editMetadata"))
        self.verticalLayout.addWidget(self.editMetadata)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.buttonBox = QtGui.QDialogButtonBox(CrayfishViewerPluginLayerPropsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(CrayfishViewerPluginLayerPropsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CrayfishViewerPluginLayerPropsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CrayfishViewerPluginLayerPropsDialog)
        CrayfishViewerPluginLayerPropsDialog.setTabOrder(self.editCRS, self.btnSpecifyCRS)
        CrayfishViewerPluginLayerPropsDialog.setTabOrder(self.btnSpecifyCRS, self.editMetadata)
        CrayfishViewerPluginLayerPropsDialog.setTabOrder(self.editMetadata, self.buttonBox)

    def retranslateUi(self, CrayfishViewerPluginLayerPropsDialog):
        CrayfishViewerPluginLayerPropsDialog.setWindowTitle(_translate("CrayfishViewerPluginLayerPropsDialog", "Dialog", None))
        self.groupBox.setTitle(_translate("CrayfishViewerPluginLayerPropsDialog", "Coordinate Reference System", None))
        self.btnSpecifyCRS.setText(_translate("CrayfishViewerPluginLayerPropsDialog", "Specify...", None))
        self.groupBox_2.setTitle(_translate("CrayfishViewerPluginLayerPropsDialog", "Metadata", None))

