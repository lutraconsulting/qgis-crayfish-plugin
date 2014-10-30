# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'upload_connection_settings_dialog_widget.ui'
#
# Created: Mon Dec 23 11:59:28 2013
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
        Dialog.resize(360, 122)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/illuvis/illuvis_u_32w.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.usernameLabel = QtGui.QLabel(Dialog)
        self.usernameLabel.setObjectName(_fromUtf8("usernameLabel"))
        self.gridLayout.addWidget(self.usernameLabel, 0, 0, 1, 1)
        self.passwordLabel = QtGui.QLabel(Dialog)
        self.passwordLabel.setObjectName(_fromUtf8("passwordLabel"))
        self.gridLayout.addWidget(self.passwordLabel, 1, 0, 1, 1)
        self.registerOnlinePushButton = QtGui.QPushButton(Dialog)
        self.registerOnlinePushButton.setObjectName(_fromUtf8("registerOnlinePushButton"))
        self.gridLayout.addWidget(self.registerOnlinePushButton, 2, 2, 1, 1)
        self.passwordLineEdit = QtGui.QLineEdit(Dialog)
        self.passwordLineEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordLineEdit.setObjectName(_fromUtf8("passwordLineEdit"))
        self.gridLayout.addWidget(self.passwordLineEdit, 1, 1, 1, 2)
        self.usernameLineEdit = QtGui.QLineEdit(Dialog)
        self.usernameLineEdit.setObjectName(_fromUtf8("usernameLineEdit"))
        self.gridLayout.addWidget(self.usernameLineEdit, 0, 1, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 3)
        self.savePassCheckBox = QtGui.QCheckBox(Dialog)
        self.savePassCheckBox.setChecked(True)
        self.savePassCheckBox.setObjectName(_fromUtf8("savePassCheckBox"))
        self.gridLayout.addWidget(self.savePassCheckBox, 2, 0, 1, 1)
        self.testConnectionPushButton = QtGui.QPushButton(Dialog)
        self.testConnectionPushButton.setObjectName(_fromUtf8("testConnectionPushButton"))
        self.gridLayout.addWidget(self.testConnectionPushButton, 2, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.registerOnlinePushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.registerButtonPressed)
        QtCore.QObject.connect(self.testConnectionPushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.testConnectButtonPressed)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.saveSettings)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.usernameLineEdit, self.passwordLineEdit)
        Dialog.setTabOrder(self.passwordLineEdit, self.savePassCheckBox)
        Dialog.setTabOrder(self.savePassCheckBox, self.testConnectionPushButton)
        Dialog.setTabOrder(self.testConnectionPushButton, self.registerOnlinePushButton)
        Dialog.setTabOrder(self.registerOnlinePushButton, self.buttonBox)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "illuvis Connection Settings", None))
        self.usernameLabel.setText(_translate("Dialog", "Username (email address)", None))
        self.passwordLabel.setText(_translate("Dialog", "Password", None))
        self.registerOnlinePushButton.setText(_translate("Dialog", "Register Online", None))
        self.savePassCheckBox.setText(_translate("Dialog", "Save Password", None))
        self.testConnectionPushButton.setText(_translate("Dialog", "Test Connection", None))

import resources_rc
