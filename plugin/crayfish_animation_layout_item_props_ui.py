# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crayfish_animation_layout_item_props.ui'
#
# Created: Wed Apr 29 15:40:05 2015
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

class Ui_AnimationLayoutItemProps(object):
    def setupUi(self, AnimationLayoutItemProps):
        AnimationLayoutItemProps.setObjectName(_fromUtf8("AnimationLayoutItemProps"))
        AnimationLayoutItemProps.resize(475, 175)
        self.formLayout = QtGui.QFormLayout(AnimationLayoutItemProps)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.lblLabel = QtGui.QLabel(AnimationLayoutItemProps)
        self.lblLabel.setObjectName(_fromUtf8("lblLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.lblLabel)
        self.editLabel = QtGui.QLineEdit(AnimationLayoutItemProps)
        self.editLabel.setObjectName(_fromUtf8("editLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.editLabel)
        self.lblTimeFormat = QtGui.QLabel(AnimationLayoutItemProps)
        self.lblTimeFormat.setObjectName(_fromUtf8("lblTimeFormat"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.lblTimeFormat)
        self.cboTimeFormat = QtGui.QComboBox(AnimationLayoutItemProps)
        self.cboTimeFormat.setObjectName(_fromUtf8("cboTimeFormat"))
        self.cboTimeFormat.addItem(_fromUtf8(""))
        self.cboTimeFormat.addItem(_fromUtf8(""))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.cboTimeFormat)
        self.lblText = QtGui.QLabel(AnimationLayoutItemProps)
        self.lblText.setObjectName(_fromUtf8("lblText"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.lblText)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnFont = QtGui.QPushButton(AnimationLayoutItemProps)
        self.btnFont.setObjectName(_fromUtf8("btnFont"))
        self.horizontalLayout.addWidget(self.btnFont)
        self.btnTextColor = QgsColorButton(AnimationLayoutItemProps)
        self.btnTextColor.setText(_fromUtf8(""))
        self.btnTextColor.setObjectName(_fromUtf8("btnTextColor"))
        self.horizontalLayout.addWidget(self.btnTextColor)
        self.formLayout.setLayout(2, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.lblBackground = QtGui.QLabel(AnimationLayoutItemProps)
        self.lblBackground.setObjectName(_fromUtf8("lblBackground"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.lblBackground)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.chkBackground = QtGui.QCheckBox(AnimationLayoutItemProps)
        self.chkBackground.setText(_fromUtf8(""))
        self.chkBackground.setObjectName(_fromUtf8("chkBackground"))
        self.horizontalLayout_2.addWidget(self.chkBackground)
        self.btnBackgroundColor = QgsColorButton(AnimationLayoutItemProps)
        self.btnBackgroundColor.setText(_fromUtf8(""))
        self.btnBackgroundColor.setObjectName(_fromUtf8("btnBackgroundColor"))
        self.horizontalLayout_2.addWidget(self.btnBackgroundColor)
        self.formLayout.setLayout(3, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.lblPosition = QtGui.QLabel(AnimationLayoutItemProps)
        self.lblPosition.setObjectName(_fromUtf8("lblPosition"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.lblPosition)
        self.cboPosition = QtGui.QComboBox(AnimationLayoutItemProps)
        self.cboPosition.setObjectName(_fromUtf8("cboPosition"))
        self.cboPosition.addItem(_fromUtf8(""))
        self.cboPosition.addItem(_fromUtf8(""))
        self.cboPosition.addItem(_fromUtf8(""))
        self.cboPosition.addItem(_fromUtf8(""))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.cboPosition)

        self.retranslateUi(AnimationLayoutItemProps)
        QtCore.QMetaObject.connectSlotsByName(AnimationLayoutItemProps)
        AnimationLayoutItemProps.setTabOrder(self.editLabel, self.cboTimeFormat)
        AnimationLayoutItemProps.setTabOrder(self.cboTimeFormat, self.btnBackgroundColor)
        AnimationLayoutItemProps.setTabOrder(self.btnBackgroundColor, self.cboPosition)

    def retranslateUi(self, AnimationLayoutItemProps):
        AnimationLayoutItemProps.setWindowTitle(_translate("AnimationLayoutItemProps", "Form", None))
        self.lblLabel.setText(_translate("AnimationLayoutItemProps", "Label", None))
        self.lblTimeFormat.setText(_translate("AnimationLayoutItemProps", "Format", None))
        self.cboTimeFormat.setItemText(0, _translate("AnimationLayoutItemProps", "hh:mm:ss.ss", None))
        self.cboTimeFormat.setItemText(1, _translate("AnimationLayoutItemProps", "hh.hhh", None))
        self.lblText.setText(_translate("AnimationLayoutItemProps", "Text", None))
        self.btnFont.setText(_translate("AnimationLayoutItemProps", "Font...", None))
        self.lblBackground.setText(_translate("AnimationLayoutItemProps", "Background", None))
        self.lblPosition.setText(_translate("AnimationLayoutItemProps", "Position", None))
        self.cboPosition.setItemText(0, _translate("AnimationLayoutItemProps", "Top-left", None))
        self.cboPosition.setItemText(1, _translate("AnimationLayoutItemProps", "Top-right", None))
        self.cboPosition.setItemText(2, _translate("AnimationLayoutItemProps", "Bottom-left", None))
        self.cboPosition.setItemText(3, _translate("AnimationLayoutItemProps", "Bottom-right", None))

from qgis.gui import QgsColorButton
