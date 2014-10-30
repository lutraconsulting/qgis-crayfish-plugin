# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'new_event_dialog_widget.ui'
#
# Created: Thu Dec 19 15:28:28 2013
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
        Dialog.resize(332, 437)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/illuvis/illuvis_u_32w.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.stormDurationLabel = QtGui.QLabel(Dialog)
        self.stormDurationLabel.setObjectName(_fromUtf8("stormDurationLabel"))
        self.gridLayout.addWidget(self.stormDurationLabel, 4, 0, 1, 1)
        self.descriptionLabel = QtGui.QLabel(Dialog)
        self.descriptionLabel.setObjectName(_fromUtf8("descriptionLabel"))
        self.gridLayout.addWidget(self.descriptionLabel, 9, 0, 1, 1)
        self.returnPeriodLabel = QtGui.QLabel(Dialog)
        self.returnPeriodLabel.setObjectName(_fromUtf8("returnPeriodLabel"))
        self.gridLayout.addWidget(self.returnPeriodLabel, 3, 0, 1, 1)
        self.modellerLabel = QtGui.QLabel(Dialog)
        self.modellerLabel.setObjectName(_fromUtf8("modellerLabel"))
        self.gridLayout.addWidget(self.modellerLabel, 5, 0, 1, 1)
        self.eventNameLabel = QtGui.QLabel(Dialog)
        self.eventNameLabel.setObjectName(_fromUtf8("eventNameLabel"))
        self.gridLayout.addWidget(self.eventNameLabel, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.modelNameLabel = QtGui.QLabel(Dialog)
        self.modelNameLabel.setObjectName(_fromUtf8("modelNameLabel"))
        self.gridLayout.addWidget(self.modelNameLabel, 6, 0, 1, 1)
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 7, 0, 1, 1)
        self.eventNamesComboBox = QtGui.QComboBox(Dialog)
        self.eventNamesComboBox.setEnabled(False)
        self.eventNamesComboBox.setObjectName(_fromUtf8("eventNamesComboBox"))
        self.gridLayout.addWidget(self.eventNamesComboBox, 11, 1, 1, 1)
        self.copyPushButton = QtGui.QPushButton(Dialog)
        self.copyPushButton.setEnabled(False)
        self.copyPushButton.setObjectName(_fromUtf8("copyPushButton"))
        self.gridLayout.addWidget(self.copyPushButton, 11, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Help|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 14, 0, 1, 3)
        self.line = QtGui.QFrame(Dialog)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout.addWidget(self.line, 10, 0, 1, 3)
        self.descriptionTextEdit = QtGui.QTextEdit(Dialog)
        self.descriptionTextEdit.setObjectName(_fromUtf8("descriptionTextEdit"))
        self.gridLayout.addWidget(self.descriptionTextEdit, 9, 1, 1, 2)
        self.climateChangeCheckBox = QtGui.QCheckBox(Dialog)
        self.climateChangeCheckBox.setObjectName(_fromUtf8("climateChangeCheckBox"))
        self.gridLayout.addWidget(self.climateChangeCheckBox, 8, 1, 1, 2)
        self.modelVersionLineEdit = QtGui.QLineEdit(Dialog)
        self.modelVersionLineEdit.setObjectName(_fromUtf8("modelVersionLineEdit"))
        self.gridLayout.addWidget(self.modelVersionLineEdit, 7, 1, 1, 2)
        self.modelNameLineEdit = QtGui.QLineEdit(Dialog)
        self.modelNameLineEdit.setObjectName(_fromUtf8("modelNameLineEdit"))
        self.gridLayout.addWidget(self.modelNameLineEdit, 6, 1, 1, 2)
        self.modellerLineEdit = QtGui.QLineEdit(Dialog)
        self.modellerLineEdit.setObjectName(_fromUtf8("modellerLineEdit"))
        self.gridLayout.addWidget(self.modellerLineEdit, 5, 1, 1, 2)
        self.stormDurationLineEdit = QtGui.QLineEdit(Dialog)
        self.stormDurationLineEdit.setObjectName(_fromUtf8("stormDurationLineEdit"))
        self.gridLayout.addWidget(self.stormDurationLineEdit, 4, 1, 1, 2)
        self.returnPeriodLineEdit = QtGui.QLineEdit(Dialog)
        self.returnPeriodLineEdit.setObjectName(_fromUtf8("returnPeriodLineEdit"))
        self.gridLayout.addWidget(self.returnPeriodLineEdit, 3, 1, 1, 2)
        self.eventNameLineEdit = QtGui.QLineEdit(Dialog)
        self.eventNameLineEdit.setObjectName(_fromUtf8("eventNameLineEdit"))
        self.gridLayout.addWidget(self.eventNameLineEdit, 2, 1, 1, 2)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 11, 0, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 3)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("helpRequested()")), Dialog.helpPressed)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.create)
        QtCore.QObject.connect(self.copyPushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.copyButtonPressed)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.eventNameLineEdit, self.returnPeriodLineEdit)
        Dialog.setTabOrder(self.returnPeriodLineEdit, self.stormDurationLineEdit)
        Dialog.setTabOrder(self.stormDurationLineEdit, self.modellerLineEdit)
        Dialog.setTabOrder(self.modellerLineEdit, self.modelNameLineEdit)
        Dialog.setTabOrder(self.modelNameLineEdit, self.modelVersionLineEdit)
        Dialog.setTabOrder(self.modelVersionLineEdit, self.climateChangeCheckBox)
        Dialog.setTabOrder(self.climateChangeCheckBox, self.descriptionTextEdit)
        Dialog.setTabOrder(self.descriptionTextEdit, self.eventNamesComboBox)
        Dialog.setTabOrder(self.eventNamesComboBox, self.copyPushButton)
        Dialog.setTabOrder(self.copyPushButton, self.buttonBox)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "New Event", None))
        self.stormDurationLabel.setText(_translate("Dialog", "Storm Duration", None))
        self.descriptionLabel.setText(_translate("Dialog", "Description", None))
        self.returnPeriodLabel.setText(_translate("Dialog", "Return Period", None))
        self.modellerLabel.setText(_translate("Dialog", "Modeller", None))
        self.eventNameLabel.setText(_translate("Dialog", "Event Name*", None))
        self.modelNameLabel.setText(_translate("Dialog", "Model Name", None))
        self.label.setText(_translate("Dialog", "Model Version", None))
        self.copyPushButton.setText(_translate("Dialog", "Copy", None))
        self.climateChangeCheckBox.setText(_translate("Dialog", "Considers Climate Change*", None))
        self.label_3.setText(_translate("Dialog", "Copy fields from:", None))
        self.label_2.setText(_translate("Dialog", "An event describes a set of boundary conditions (or storm event) that has been applied to a scenario. Click Help for more details.", None))

import resources_rc
