# -*- coding: utf-8 -*-

# illuvis - Tools for the effective communication of flood risk
# Copyright (C) 2014 Lutra Consulting

# info at lutraconsulting dot co dot uk
# Lutra Consulting
# 23 Chestnut Close
# Burgess Hill
# West Sussex
# RH15 8HN

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import traceback
from illuvis_interface import *

from upload_connection_settings_dialog_widget import Ui_Dialog

class ConSettingsDialog(QDialog, Ui_Dialog):
    
    def __init__(self, parent):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.usernameLineEdit.setFocus()
        self.parent = parent
        self.ilCon = self.parent.ilCon
        
        # Retrieve settings if existing
        s = QSettings()
        uName = s.value("illuvisUpload/username", '', type=str)
        pWord = s.value("illuvisUpload/password", '', type=str)
        storePass = s.value("illuvisUpload/storePassword", True, type=bool)
        self.usernameLineEdit.setText(uName)
        self.passwordLineEdit.setText(pWord)
        self.savePassCheckBox.setChecked(storePass)
        
        # Disconnect parent's slots
        self.ilCon.processedListProjectsResponseSignal.disconnect(self.parent.handleRefreshProjects)
        self.ilCon.processedListProjectsResponseSignal.connect(self.handleRefreshProjects)
        self.ilCon.requestFailedSignal.disconnect(self.parent.reportError)
        self.ilCon.requestFailedSignal.connect(self.reportError)
        
        self.ilCon.requestStartedSignal.disconnect(self.parent.freezeUi)
        self.ilCon.requestProgressChangedSignal.disconnect(self.parent.handleProgressChanged)
        self.ilCon.requestFinishedSignal.disconnect(self.parent.handleRequestFinished)
        
    def __del__(self):
        # Re-connect parent's slots
        self.ilCon.requestFailedSignal.disconnect(self.reportError)
        self.ilCon.requestFailedSignal.connect(self.parent.reportError)
        self.ilCon.processedListProjectsResponseSignal.disconnect(self.handleRefreshProjects)
        self.ilCon.processedListProjectsResponseSignal.connect(self.parent.handleRefreshProjects)
        
        self.ilCon.requestStartedSignal.connect(self.parent.freezeUi)
        self.ilCon.requestProgressChangedSignal.connect(self.parent.handleProgressChanged)
        self.ilCon.requestFinishedSignal.connect(self.parent.handleRequestFinished)
        
    def handleRefreshProjects(self, projects):
        QMessageBox.information(self, 'Test Connection', 'Connection was successful')
        
    def reportError(self, err):
        QMessageBox.critical(self, 'Test Connection', 'The following error occured when connecting: %s' % err)
    
    
    def setPasswordFieldFocus(self):
        self.passwordLineEdit.setFocus()
    
    
    def testConnectButtonPressed(self):
        uName = self.usernameLineEdit.text()
        pWord = self.passwordLineEdit.text()
        self.ilCon.setCredentials(uName, pWord)
        self.ilCon.testConnect()
        
        
    def saveSettings(self):
        """ Save any settings """
        uName = self.usernameLineEdit.text()
        pWord = self.passwordLineEdit.text()
        s = QSettings()
        s.setValue('illuvisUpload/username', uName)
        if self.savePassCheckBox.isChecked():
            # Store the credential
            reply = QMessageBox.question(self, 'Saving passwords', \
                    'WARNING: You have opted to save your password. It will be stored in plain text in your project files and in your home directory on Unix-like systems, or in your user profile on Windows. If you do not want this to happen, please press the Cancel button.', \
                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            # User gives consent...
            s.setValue('illuvisUpload/password', pWord)
            s.setValue('illuvisUpload/storePassword', True)
        else:
            s.remove('illuvisUpload/password')
            s.setValue('illuvisUpload/storePassword', False)
        self.parent.ilCon.setCredentials(uName, pWord)
        self.accept()
    
    
    def registerButtonPressed(self):
        # Open the illuvis reg page
        QDesktopServices.openUrl(QUrl('https://www.illuvis.com/auth.php?mode=register'))
