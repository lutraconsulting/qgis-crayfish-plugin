# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_about_dialog_widget.ui'
#
# Created: Thu Nov  6 17:59:20 2014
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(518, 306)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.crayfishIconLabel = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.crayfishIconLabel.sizePolicy().hasHeightForWidth())
        self.crayfishIconLabel.setSizePolicy(sizePolicy)
        self.crayfishIconLabel.setMinimumSize(QtCore.QSize(128, 128))
        self.crayfishIconLabel.setText(_fromUtf8(""))
        self.crayfishIconLabel.setObjectName(_fromUtf8("crayfishIconLabel"))
        self.verticalLayout.addWidget(self.crayfishIconLabel)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.lutraLogoLabel = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lutraLogoLabel.sizePolicy().hasHeightForWidth())
        self.lutraLogoLabel.setSizePolicy(sizePolicy)
        self.lutraLogoLabel.setMinimumSize(QtCore.QSize(200, 69))
        self.lutraLogoLabel.setText(_fromUtf8(""))
        self.lutraLogoLabel.setObjectName(_fromUtf8("lutraLogoLabel"))
        self.verticalLayout.addWidget(self.lutraLogoLabel)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.aboutBrowser = QtGui.QTextBrowser(Dialog)
        self.aboutBrowser.setAcceptRichText(False)
        self.aboutBrowser.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.aboutBrowser.setOpenExternalLinks(True)
        self.aboutBrowser.setOpenLinks(True)
        self.aboutBrowser.setObjectName(_fromUtf8("aboutBrowser"))
        self.horizontalLayout.addWidget(self.aboutBrowser)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "About Crayfish", None))

