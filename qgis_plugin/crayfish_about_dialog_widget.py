# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_about_dialog_widget.ui'
#
# Created: Sat Sep 21 22:14:33 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(400, 252)
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
        self.lutraLogoLabel.setMinimumSize(QtCore.QSize(128, 46))
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
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "About Crayfish", None, QtGui.QApplication.UnicodeUTF8))
        self.aboutBrowser.setHtml(QtGui.QApplication.translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\" bgcolor=\"#efe1bb\">\n"
"<p style=\" margin-top:18px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'FreeSans,Geneva,Arial,sans-serif\'; font-size:8pt; font-weight:600; color:#412824;\">Crayfish Plugin</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'FreeSans,Geneva,Arial,sans-serif\'; font-size:8pt; color:#412824;\">The Crayfish Plugin is a collection of tools for hydraulic modellers working with TUFLOW and other modelling packages. It aims to use QGIS as an efficient and effective pre and post-processor.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'FreeSans,Geneva,Arial,sans-serif\'; font-size:8pt; color:#412824;\">Check out the </span><a href=\"http://www.lutraconsulting.co.uk/resources/crayfish\"><span style=\" font-family:\'FreeSans,Geneva,Arial,sans-serif\'; font-size:8pt; text-decoration: underline; color:#412824;\">Crayfish resources page</span></a><span style=\" font-family:\'FreeSans,Geneva,Arial,sans-serif\'; font-size:8pt; color:#412824;\"> on our website for more information.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

