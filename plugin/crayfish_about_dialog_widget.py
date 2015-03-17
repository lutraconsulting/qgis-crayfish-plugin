# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_about_dialog_widget.ui'
#
# Created: Wed Nov 12 14:13:30 2014
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
        Dialog.resize(466, 566)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabAbout = QtGui.QWidget()
        self.tabAbout.setObjectName(_fromUtf8("tabAbout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.tabAbout)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.aboutBrowser = QtWebKit.QWebView(self.tabAbout)
        self.aboutBrowser.setObjectName(_fromUtf8("aboutBrowser"))
        self.verticalLayout_2.addWidget(self.aboutBrowser)
        self.tabWidget.addTab(self.tabAbout, _fromUtf8(""))
        self.tabNews = QtGui.QWidget()
        self.tabNews.setObjectName(_fromUtf8("tabNews"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tabNews)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.newsBrowser = QtWebKit.QWebView(self.tabNews)
        self.newsBrowser.setObjectName(_fromUtf8("newsBrowser"))
        self.verticalLayout_3.addWidget(self.newsBrowser)
        self.tabWidget.addTab(self.tabNews, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "About Crayfish", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAbout), _translate("Dialog", "About", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabNews), _translate("Dialog", "What\'s new", None))

from PyQt4 import QtWebKit
