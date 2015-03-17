# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'new_scenario_dialog_widget.ui'
#
# Created: Thu Dec 19 15:28:33 2013
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
        Dialog.resize(314, 247)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/illuvis/illuvis_u_32w.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.descriptionLabel = QtGui.QLabel(Dialog)
        self.descriptionLabel.setObjectName(_fromUtf8("descriptionLabel"))
        self.gridLayout.addWidget(self.descriptionLabel, 3, 0, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Help|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.scenarioNameLabel = QtGui.QLabel(Dialog)
        self.scenarioNameLabel.setObjectName(_fromUtf8("scenarioNameLabel"))
        self.gridLayout.addWidget(self.scenarioNameLabel, 2, 0, 1, 1)
        self.scenarioNameLineEdit = QtGui.QLineEdit(Dialog)
        self.scenarioNameLineEdit.setObjectName(_fromUtf8("scenarioNameLineEdit"))
        self.gridLayout.addWidget(self.scenarioNameLineEdit, 2, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.descriptionTextEdit = QtGui.QTextEdit(Dialog)
        self.descriptionTextEdit.setObjectName(_fromUtf8("descriptionTextEdit"))
        self.gridLayout.addWidget(self.descriptionTextEdit, 3, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("helpRequested()")), Dialog.helpPressed)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.create)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.scenarioNameLineEdit, self.descriptionTextEdit)
        Dialog.setTabOrder(self.descriptionTextEdit, self.buttonBox)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "New Scenario", None))
        self.descriptionLabel.setText(_translate("Dialog", "Description", None))
        self.label_2.setText(_translate("Dialog", "Each project contains 1 or more scenarios.  Scenarios are used to describe the configuration of the model during a given storm event, for example, \'Baseline\', \'Undefended\' or \'Porposed\'. Click Help for more details.", None))
        self.scenarioNameLabel.setText(_translate("Dialog", "Scenario Name*", None))

import resources_rc
