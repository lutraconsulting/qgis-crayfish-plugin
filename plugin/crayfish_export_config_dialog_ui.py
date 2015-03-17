# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_export_config_dialog.ui'
#
# Created: Fri Oct 31 11:07:49 2014
#      by: PyQt4 UI code generator 4.10.4
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

class Ui_CrayfishExportConfigDialog(object):
    def setupUi(self, CrayfishExportConfigDialog):
        CrayfishExportConfigDialog.setObjectName(_fromUtf8("CrayfishExportConfigDialog"))
        CrayfishExportConfigDialog.resize(239, 136)
        self.verticalLayout = QtGui.QVBoxLayout(CrayfishExportConfigDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(CrayfishExportConfigDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.spinResolution = QtGui.QDoubleSpinBox(CrayfishExportConfigDialog)
        self.spinResolution.setMinimum(0.25)
        self.spinResolution.setMaximum(9999.99)
        self.spinResolution.setProperty("value", 2.0)
        self.spinResolution.setObjectName(_fromUtf8("spinResolution"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.spinResolution)
        self.chkAddToCanvas = QtGui.QCheckBox(CrayfishExportConfigDialog)
        self.chkAddToCanvas.setObjectName(_fromUtf8("chkAddToCanvas"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.SpanningRole, self.chkAddToCanvas)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtGui.QDialogButtonBox(CrayfishExportConfigDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CrayfishExportConfigDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CrayfishExportConfigDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CrayfishExportConfigDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CrayfishExportConfigDialog)

    def retranslateUi(self, CrayfishExportConfigDialog):
        CrayfishExportConfigDialog.setWindowTitle(_translate("CrayfishExportConfigDialog", "Export to Raster Grid", None))
        self.label.setText(_translate("CrayfishExportConfigDialog", "Grid resolution", None))
        self.spinResolution.setSuffix(_translate("CrayfishExportConfigDialog", " m", None))
        self.chkAddToCanvas.setText(_translate("CrayfishExportConfigDialog", "Add result to canvas", None))

