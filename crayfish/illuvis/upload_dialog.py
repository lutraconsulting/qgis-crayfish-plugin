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

from upload_dialog_widget import Ui_Dialog
from illuvis_interface import *
import upload_connection_settings_dialog
import new_project_dialog
import new_overlay_dialog
import new_scenario_dialog
import new_event_dialog

from ..gui.utils import time_to_string

import os
import tempfile
import traceback
import zipfile
import base64
import glob

class ResultPrepper(QThread):
    
    def __init__(self):
        QThread.__init__(self)
    
    def __del__(self):
        self.wait()
        
    def configure(self, tmpArchiveFilePath, resultFilePath, fileType, resultPrjFilePath, eventId):
        self.tmpArchiveFilePath = tmpArchiveFilePath
        self.resultFilePath = resultFilePath
        self.fileType = fileType
        self.resultPrjFilePath = resultPrjFilePath
        self.eventId = eventId
 
    def run(self):
        """ This function is intended to be run in a seperate thread and 
        is responsible for compressing and encoding the data to be sent 
        to the server. """
        
        try:
            with zipfile.ZipFile(self.tmpArchiveFilePath, 'w', zipfile.ZIP_DEFLATED) as z:
                z.write(self.resultFilePath, self.fileType+'.tif')
                if os.path.isfile(self.resultPrjFilePath):
                    z.write(self.resultPrjFilePath, self.fileType+'.prj')
        except:
            msg = traceback.format_exc()
            self.emit( SIGNAL('failed(QString)'), msg)
            return
            
        with open(self.tmpArchiveFilePath, "rb") as binFile:
            base64Data = base64.b64encode(binFile.read())
        fileData = ('file_data', self.tmpArchiveFilePath, base64Data)
        
        self.emit( SIGNAL('prep_completed(int, QString, QString, QString, QString)'), self.eventId, self.fileType, fileData[0], fileData[1], fileData[2])
        return


class MessageDialog(QDialog):
    """ Message dialog that remembers whether it should not be shown again """
    def __init__(self, dlgId, text, title, parent=None):
        QDialog.__init__(self)
        self.dlgId = dlgId

        self.tb = QTextBrowser()
        self.tb.setHtml(text)
        self.tb.anchorClicked.connect(QDesktopServices.openUrl)
        self.tb.setOpenExternalLinks(True)
        self.tb.setOpenLinks(True)
        self.chk = QCheckBox("Don't show this message again")
        self.bb = QDialogButtonBox(QDialogButtonBox.Ok)
        l = QVBoxLayout()
        for w in [self.tb, self.chk, self.bb]: l.addWidget(w)
        self.setLayout(l)

        self.setWindowTitle(title)
        self.resize(400,300)
        self.bb.accepted.connect(self.accept)

    def exec_(self):
        if QSettings().value("crayfishViewer/noShow_"+self.dlgId):
           return
        QDialog.exec_(self)

    def accept(self):
        if self.chk.isChecked():
            QSettings().setValue("crayfishViewer/noShow_"+self.dlgId, 1)
        QDialog.accept(self)


class UploadDialog(QDialog, Ui_Dialog):
    
    def __init__(self, iface, currentLayer=None):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.connected = False
        self.frozen = False
        self.iface = iface
        self.layer = currentLayer

        self.statusLabel.setText('')
        self.ilCon = IlluvisInterface()
        self.resultPrepper = ResultPrepper()
        
        # Make connections
        self.ilCon.processedListProjectsResponseSignal.connect(self.handleRefreshProjects)
        self.ilCon.processedListScenariosResponseSignal.connect(self.handleRefreshScenarios)
        self.ilCon.processedListOverlaysResponseSignal.connect(self.handleRefreshOverlays)
        self.ilCon.processedListEventsResponseSignal.connect(self.handleRefreshEvents)
        self.ilCon.processedDiskUsageResponseSignal.connect(self.handleDiskUsage)
        self.ilCon.processedUploadDataResponseSignal.connect(self.handleUploadData)
        self.ilCon.processedUploadOverlayResponseSignal.connect(self.handleUploadOverlay)
        self.ilCon.requestProgressChangedSignal.connect(self.handleProgressChanged)
        self.ilCon.requestStartedSignal.connect(self.freezeUi)
        self.ilCon.requestFinishedSignal.connect(self.handleRequestFinished)
        self.ilCon.requestFailedSignal.connect(self.reportError)
        
        self.connect( self.resultPrepper, SIGNAL("prep_completed(int, QString, QString, QString, QString)"), self.onPreparationSucceeded )
        self.connect( self.resultPrepper, SIGNAL("failed(QString)"), self.onPreparationFailed )
        
        self.supportedResultTypes = ['Depth', 'Velocity']
        for sR in self.supportedResultTypes:
            self.resultTypeComboBox.addItem(sR)

        if self.layer:
            ds = self.layer.currentDataSet()
            name = self.layer.name() + " / " + ds.name()
            if ds.time_varying():
              output = self.layer.currentOutputForDataset(ds)
              name += " @ " + time_to_string(output.time())
            self.fromCurrentRadioButton.setText("From current layer: " + name)
        else:
            self.fromFileRadioButton.setChecked(True)
            self.fromCurrentRadioButton.setText("From current layer: (none)")
            self.fromCurrentRadioButton.setEnabled(False)

        self.labelInfo.linkActivated.connect(self.openLink)

        self.fromCurrentRadioButton.clicked.connect(self.updateResultSourceGUI)
        self.fromFileRadioButton.clicked.connect(self.updateResultSourceGUI)
        self.updateResultSourceGUI()

        self.setStoredStates()
        self.progressBar.setVisible(False)

        self.connectedAsLabel.setText('Connected as: [Not connected]')
        self.freezeUi('', omitConnectButton=True, omitButtonBox=True)
        
        # Attempt to connect
        s = QSettings()
        uName = s.value("illuvisUpload/username", '', type=str)
        pWord = s.value("illuvisUpload/password", '', type=str)
        if len(uName) > 0 and len(pWord) > 0:
            # We retrieved both, set them and connect
            self.connectToServer(username=uName, password=pWord, quiet=True)
        elif len(uName) > 0 and len(pWord) == 0:
            # Either there was no stored password, or the connection 
            # attempt failed
            self.connectionSettingsButtonPressed(promptingForPassword=True)
        else:
            # There was not even a username, simple open the dialog and 
            # do not connect.
            pass

    
    def __del__(self):
        self.disconnect( self.resultPrepper, SIGNAL("failed(QString)"), self.onPreparationFailed )
        self.disconnect( self.resultPrepper, SIGNAL("prep_completed(int, QString, QString, QString, QString)"), self.onPreparationSucceeded )
        
        self.ilCon.requestFailedSignal.disconnect(self.reportError)
        self.ilCon.requestFinishedSignal.disconnect(self.handleRequestFinished)
        self.ilCon.requestStartedSignal.disconnect(self.freezeUi)
        self.ilCon.requestProgressChangedSignal.disconnect(self.handleProgressChanged)
        self.ilCon.processedUploadOverlayResponseSignal.disconnect(self.handleUploadOverlay)
        self.ilCon.processedUploadDataResponseSignal.disconnect(self.handleUploadData)
        self.ilCon.processedDiskUsageResponseSignal.disconnect(self.handleDiskUsage)
        self.ilCon.processedListEventsResponseSignal.disconnect(self.handleRefreshEvents)
        self.ilCon.processedListOverlaysResponseSignal.disconnect(self.handleRefreshOverlays)
        self.ilCon.processedListScenariosResponseSignal.disconnect(self.handleRefreshScenarios)
        self.ilCon.processedListProjectsResponseSignal.disconnect(self.handleRefreshProjects)
        
        
    def handleRequestFinished(self):
        self.progressBar.setVisible(False)
        self.statusLabel.setText('')
        if self.connected:
            self.thawUi()
        
    def reportError(self, msg):
        self.progressBar.setVisible(False)
        self.statusLabel.setText('')
        if msg == 'Authentication failed':
            self.connectionSettingsButtonPressed(promptingForPassword=True)
        else:
            QMessageBox.critical(self, 'illuvis Request Failed', msg)
    
    def handleProgressChanged(self, pctComplete):
        if pctComplete < 100:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(100)
            self.progressBar.setValue(pctComplete)
        else:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(0)
            self.statusLabel.setText('Processing data on server - Please be patient...')
            
    
    def updateDiskUsageBar(self):
        self.ilCon.diskUsage()
    
    def handleDiskUsage(self, used, total):
        self.diskUseProgressBar.setVisible(True)
        self.diskUseProgressBar.setMinimum(0)
        self.diskUseProgressBar.setMaximum(total)
        if used < total:
            self.diskUseProgressBar.setFormat('%v MB')
            self.diskUseProgressBar.setValue(used)
        else:
            self.diskUseProgressBar.setFormat('%d MB over your limit' % (used - total))
            self.diskUseProgressBar.setValue(total)
    
    def connectToServer(self, username=None, password=None, quiet=False):
        """ Attempt to connect to the server and refresh the project 
        list on success.  If uName and pWord are None, assume that the 
        illuvis interface already has credentials set. """
        connectionFailed = False
        if username is not None and password is not None:
            self.ilCon.setCredentials(username, password)
        self.ilCon.testConnect()
        
    def refreshProjects(self):
        self.ilCon.listProjects()
    
    def handleRefreshProjects(self, projects):
        self.connectedAsLabel.setText('Connected as: %s' % self.ilCon.username)
        self.connected = True
        self.projectComboBox.clear()
        self.scenarioComboBox.clear()
        self.overlayComboBox.clear()
        self.eventComboBox.clear()
        highestId = 0
        newestProjectComboId = 0
        newestProjectComboCounter = 0
        for proj in projects:
            if proj['editable'].lower() == 'true':
                # Only list projects for which the user can edit.
                self.projectComboBox.addItem(proj['name'])
                if proj['id'] > highestId:
                    highestId = proj['id']
                    newestProjectComboId = newestProjectComboCounter
                newestProjectComboCounter += 1
                    
        if self.projectComboBox.count() > 0:
            self.projectComboBox.setCurrentIndex(newestProjectComboId)
            self.newScenarioPushButton.setEnabled(True)
            self.newScenarioPushButtonState = True
            self.newOverlayPushButton.setEnabled(True)
            self.newOverlayPushButtonState = True
            self.deleteProjectPushButton.setEnabled(True)
            self.deleteProjectPushButtonState = True
        else:
            self.newScenarioPushButton.setEnabled(False)
            self.newScenarioPushButtonState = False
            self.newEventPushButton.setEnabled(False)
            self.newEventPushButtonState = False
            self.newOverlayPushButton.setEnabled(False)
            self.newOverlayPushButtonState = False
            self.deleteProjectPushButton.setEnabled(False)
            self.deleteProjectPushButtonState = False
            self.deleteScenarioPushButton.setEnabled(False)
            self.deleteScenarioPushButtonState = False
            self.deleteEventPushButton.setEnabled(False)
            self.deleteEventPushButtonState = False
            self.deleteOverlayPushButton.setEnabled(False)
            self.deleteOverlayPushButtonState = False
        self.updateDiskUsageBar()
        
    
    def projectComboBoxChanged(self):
        self.refreshScenarios()
        self.refreshOverlays()
    
    
    def refreshOverlays(self):
        projectId = self.projectComboBox.currentIndex()
        if projectId >= 0:
            self.ilCon.listOverlays(projectId)
    
    
    def refreshScenarios(self):
        projectId = self.projectComboBox.currentIndex()
        if projectId >= 0:
            self.ilCon.listScenarios(projectId)
    
    
    def handleRefreshScenarios(self, scenarios):
        
        self.scenarioComboBox.clear()
        self.eventComboBox.clear()
        
        highestId = 0
        newestScenarioComboId = 0
        newestScenarioComboCounter = 0
        for scen in scenarios:
            self.scenarioComboBox.addItem(scen['name'])
            if scen['id'] > highestId:
                highestId = scen['id']
                newestScenarioComboId = newestScenarioComboCounter
            newestScenarioComboCounter += 1
            
        if self.scenarioComboBox.count() > 0:
            self.scenarioComboBox.setCurrentIndex(newestScenarioComboId)
            self.newEventPushButton.setEnabled(True)
            self.newEventPushButtonState = True
            self.deleteScenarioPushButton.setEnabled(True)
            self.deleteScenarioPushButtonState = True
        else:
            self.newEventPushButton.setEnabled(False)
            self.newEventPushButtonState = False
            self.deleteScenarioPushButton.setEnabled(False)
            self.deleteScenarioPushButtonState = False
            self.deleteEventPushButton.setEnabled(False)
            self.deleteEventPushButtonState = False
    
    
    def handleRefreshOverlays(self, overlays):
        
        self.overlayComboBox.clear()
        for ov in overlays:
            self.overlayComboBox.addItem(ov['name'])
        if self.overlayComboBox.count() > 0:
            self.deleteOverlayPushButton.setEnabled(True)
            self.deleteOverlayPushButtonState = True
        else:
            self.deleteOverlayPushButton.setEnabled(False)
            self.deleteOverlayPushButtonState = False
                
                
    def handleRefreshEvents(self, events):
        self.eventComboBox.clear()
        
        highestId = 0
        newestEventComboId = 0
        newestEventComboCounter = 0
        for ev in events:
            self.eventComboBox.addItem(ev['name'])
            if ev['id'] > highestId:
                highestId = ev['id']
                newestEventComboId = newestEventComboCounter
            newestEventComboCounter += 1
            
        if self.eventComboBox.count() > 0:
            self.eventComboBox.setCurrentIndex(newestEventComboId)
            self.deleteEventPushButton.setEnabled(True)
            self.deleteEventPushButtonState = True
            self.updateResultSourceGUI()
            self.resolutionSpinBoxState = self.resolutionSpinBox.isEnabled()
            self.resultFileLineEditState = self.resultFileLineEdit.isEnabled()
            self.browsePushButtonState = self.browsePushButton.isEnabled()
            self.resultTypeComboBox.setEnabled(True)
            self.resultTypeComboBoxState = True
            self.uploadPushButton.setEnabled(True)
            self.uploadPushButtonState = True
        else:
            self.deleteEventPushButton.setEnabled(False)
            self.deleteEventPushButtonState = False
            self.resolutionSpinBox.setEnabled(False)
            self.resolutionSpinBoxState = False
            self.resultFileLineEdit.setEnabled(False)
            self.resultFileLineEditState = False
            self.browsePushButton.setEnabled(False)
            self.browsePushButtonState = False
            self.resultTypeComboBox.setEnabled(False)
            self.resultTypeComboBoxState = False
            self.uploadPushButton.setEnabled(False)
            self.uploadPushButtonState = False
    
    def refreshEvents(self):
        self.eventComboBox.clear()
        if self.scenarioComboBox.count() > 0:
            scenId = self.scenarioComboBox.currentIndex()
            self.ilCon.listEvents(scenId)
        
    def connectionSettingsButtonPressed(self, connect=True, promptingForPassword=False):
        d = upload_connection_settings_dialog.ConSettingsDialog(self)
        d.show()
        if promptingForPassword:
            d.setPasswordFieldFocus()
        dialogAccepted = d.exec_()
        if connect and dialogAccepted:
            self.connectToServer()
        elif promptingForPassword and not dialogAccepted:
            # The user pressed cancel, disable the UI
            self.freezeUi('', omitConnectButton=True, omitButtonBox=True)
            self.connectedAsLabel.setText('Connected as: [Not connected]')
            self.connected = False

    def setStoredStates(self, omitConnectButton=False, omitButtonBox=False):
        if not omitConnectButton:
            self.connectionSettingsPushButtonState = self.connectionSettingsPushButton.isEnabled()
        if not omitButtonBox:
            self.buttonBoxState = self.buttonBox.isEnabled()
        self.projectComboBoxState = self.projectComboBox.isEnabled()
        self.deleteProjectPushButtonState = self.deleteProjectPushButton.isEnabled()
        self.newProjectPushButtonState = self.newProjectPushButton.isEnabled()
        self.scenarioComboBoxState = self.scenarioComboBox.isEnabled()
        self.deleteScenarioPushButtonState = self.deleteScenarioPushButton.isEnabled()
        self.newScenarioPushButtonState = self.newScenarioPushButton.isEnabled()
        self.newOverlayPushButtonState = self.newOverlayPushButton.isEnabled()
        self.eventComboBoxState = self.eventComboBox.isEnabled()
        self.deleteEventPushButtonState = self.deleteEventPushButton.isEnabled()
        self.newEventPushButtonState = self.newEventPushButton.isEnabled()
        self.overlayComboBoxState = self.overlayComboBox.isEnabled()
        self.newOverlayPushButtonState = self.newOverlayPushButton.isEnabled()
        self.deleteOverlayPushButtonState = self.deleteOverlayPushButton.isEnabled()
        self.fromCurrentRadioButtonState = self.fromCurrentRadioButton.isEnabled()
        self.fromFileRadioButtonState = self.fromFileRadioButton.isEnabled()
        self.resolutionSpinBoxState = self.resolutionSpinBox.isEnabled()
        self.resultFileLineEditState = self.resultFileLineEdit.isEnabled()
        self.browsePushButtonState = self.browsePushButton.isEnabled()
        self.resultTypeComboBoxState = self.resultTypeComboBox.isEnabled()
        self.uploadPushButtonState = self.uploadPushButton.isEnabled()
    
    def freezeUi(self, statusText, omitConnectButton=False, omitButtonBox=False):
        if self.frozen:
            return
        
        self.setStoredStates(omitConnectButton=omitConnectButton, omitButtonBox=omitButtonBox)
        
        if not omitConnectButton:
            self.connectionSettingsPushButton.setEnabled( False )
        if not omitButtonBox:
            self.buttonBox.setEnabled( False )
        self.projectComboBox.setEnabled( False )
        self.deleteProjectPushButton.setEnabled( False )
        self.newProjectPushButton.setEnabled( False )
        self.scenarioComboBox.setEnabled( False )
        self.deleteScenarioPushButton.setEnabled( False )
        self.newScenarioPushButton.setEnabled( False )
        self.eventComboBox.setEnabled( False )
        self.deleteEventPushButton.setEnabled( False )
        self.newEventPushButton.setEnabled( False )
        self.overlayComboBox.setEnabled( False )
        self.newOverlayPushButton.setEnabled( False )
        self.deleteOverlayPushButton.setEnabled( False )
        self.fromCurrentRadioButton.setEnabled( False )
        self.fromFileRadioButton.setEnabled( False )
        self.resolutionSpinBox.setEnabled( False )
        self.resultFileLineEdit.setEnabled( False )
        self.browsePushButton.setEnabled( False )
        self.resultTypeComboBox.setEnabled( False )
        self.uploadPushButton.setEnabled( False )
        
        
        
        self.statusLabel.setText(statusText)
        self.frozen = True


    def thawUi(self):
        if not self.frozen:
            return
        self.connectionSettingsPushButton.setEnabled( self.connectionSettingsPushButtonState )
        self.projectComboBox.setEnabled( self.projectComboBoxState )
        self.deleteProjectPushButton.setEnabled( self.deleteProjectPushButtonState )
        self.newProjectPushButton.setEnabled( self.newProjectPushButtonState )
        self.scenarioComboBox.setEnabled( self.scenarioComboBoxState )
        self.deleteScenarioPushButton.setEnabled( self.deleteScenarioPushButtonState )
        self.newScenarioPushButton.setEnabled( self.newScenarioPushButtonState )
        self.newOverlayPushButton.setEnabled( self.newOverlayPushButtonState )
        self.eventComboBox.setEnabled( self.eventComboBoxState )
        self.deleteEventPushButton.setEnabled( self.deleteEventPushButtonState )
        self.newEventPushButton.setEnabled( self.newEventPushButtonState )
        self.overlayComboBox.setEnabled( self.overlayComboBoxState )
        self.newOverlayPushButton.setEnabled( self.newOverlayPushButtonState )
        self.deleteOverlayPushButton.setEnabled( self.deleteOverlayPushButtonState )
        self.fromCurrentRadioButton.setEnabled( self.fromCurrentRadioButtonState )
        self.fromFileRadioButton.setEnabled( self.fromFileRadioButtonState )
        self.resolutionSpinBox.setEnabled( self.resolutionSpinBoxState )
        self.resultFileLineEdit.setEnabled( self.resultFileLineEditState )
        self.browsePushButton.setEnabled( self.browsePushButtonState )
        self.resultTypeComboBox.setEnabled( self.resultTypeComboBoxState )
        self.buttonBox.setEnabled( self.buttonBoxState )
        self.uploadPushButton.setEnabled( self.uploadPushButtonState )
        
        self.statusLabel.setText('')
        self.frozen = False
        
    def uploadOverlay(self, overlayData):
        """ The overlay data should have already been checked in the 
        add overlay dialog. """
        
        originalFilePath = overlayData['layer'].publicSource()
        
        # Create the archive
        tmpArchiveFilePath, dummy = os.path.splitext(originalFilePath)
        self.tmpArchiveFilePath = tmpArchiveFilePath + '.zip'
        
        # Determine what we are adding to the archive
        manifest = []
        for shpComponent in glob.glob(tmpArchiveFilePath + '.*'):
            path, name = os.path.split(shpComponent)
            pre, ext = os.path.splitext(name)
            manifest.append( (shpComponent, 'overlay'+ext) )
        
        try:
            with zipfile.ZipFile(self.tmpArchiveFilePath, 'w') as z:
                for src, dst in manifest:
                    z.write(src, dst)
        except:
            QMessageBox.critical(self, 'Upload Overlay', 'The following unexpected error occured when trying to compress the overlay: %s' % traceback.format_exc())
            return
            
        self.statusLabel.setText('Encoding overlay')
        with open(self.tmpArchiveFilePath, "rb") as binFile:
            base64Data = base64.b64encode(binFile.read())
        fileData = ('file_data', self.tmpArchiveFilePath, base64Data)
        self.statusLabel.setText('Sending overlay')
        failed = False
        self.dataSent = 0.0
        self.progressBar.reset()
        self.progressBar.setVisible(True)
        projectId = self.projectComboBox.currentIndex()
        self.ilCon.uploadOverlay(   projectId, 
                                    overlayData.get('label_column', None), 
                                    overlayData['name'], 
                                    fileData)
        
    
    def accept(self):
        """ Upload the selected TIF file 
            First check:
                We have an event selected
        """
        
        if self.eventComboBox.count() < 1:
            QMessageBox.critical(self, 'Upload Result', 'Please first select an event into which to upload the result')
            return
        
        eventId = self.eventComboBox.currentIndex()
        fileType = self.resultTypeComboBox.currentText().lower()

        fromCurrent = self.fromCurrentRadioButton.isChecked()

        if fromCurrent:
            res = self.resolutionSpinBox.value()
            if res < 10:
              msg = """The file you're uploading has a higher resolution (%.2fm) than that supported
              by your current account type and will be resampled to 10m.<p>
              Please see <a href="https://www.illuvis.com/plans">illuvis pricing plans</a> for more options."""
              msg = msg % res
              d = MessageDialog("warnResample", msg, "Results will be downscaled", self)
              d.exec_()

            crsWkt = self.layer.crs().toWkt()
            resultFilePath = os.path.join(tempfile.gettempdir(), 'crayfish-illuvis-export.tif')
            try:
                res = self.layer.currentOutput().export_grid(res, resultFilePath, crsWkt)
            except OSError: # delayed loading of GDAL failed (windows only)
                QMessageBox.critical(None, "Crayfish", "Export failed due to incompatible "
                  "GDAL library - try to upgrade your QGIS installation to a newer version.")
                return
            if not res:
                QMessageBox.critical(None, "Crayfish", "Failed to export to raster grid")
                return
        else:
            resultFilePath = self.resultFileLineEdit.text()
            if len(resultFilePath) < 1:
                QMessageBox.critical(self, 'Upload Result', 'Please specify a result file to upload')
                return
        
        if not os.path.isfile(resultFilePath):
            QMessageBox.critical(self, 'Upload Result', '%s does not appear to be a valid file' % resultFilePath)
            return
            
        # Create the archive
        tmpArchiveFilePath, dummy = os.path.splitext(resultFilePath)
        self.tmpArchiveFilePath = tmpArchiveFilePath + '.zip'
        resultPrjFilePath = tmpArchiveFilePath + '.prj'
        
        self.resultPrepper.configure(self.tmpArchiveFilePath, resultFilePath, fileType, resultPrjFilePath, eventId)
        self.resultPrepper.start()

        self.freezeUi('Preparing data for upload')
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.reset()
        self.progressBar.setVisible(True)
        
        
    def onPreparationFailed(self, msg):
        QMessageBox.critical(self, 'Upload Result', 'The following unexpected error occured when trying to compress the result: %s' % msg)
        self.progressBar.setVisible(False)
    
    
    def onPreparationSucceeded(self, eventId, fileType, fileData_1, fileData_2, fileData_3):
        """ This function is called by the thread which is responsible 
        for handling the compression and encoding of the data for 
        uplaod. """
        fileData = (fileData_1, fileData_2, fileData_3)
        self.statusLabel.setText('Sending result')
        failed = False
        self.dataSent = 0.0
        self.ilCon.uploadData(eventId, fileType, fileData)
        
    
    def handleUploadData(self):
        QMessageBox.information(self, 'Upload Result', 'Upload complete')
        try:
            os.remove(self.tmpArchiveFilePath)
        except:
            QMessageBox.warning(self, 'Upload Result', 'Failed to remove temporary file %s' % self.tmpArchiveFilePath)
        self.statusLabel.setText('')
        self.progressBar.setVisible(False)
        self.uploadPushButton.setText('Upload')
        self.uploadPushButton.setEnabled(True)
        self.updateDiskUsageBar()
        
    
    def handleUploadOverlay(self):
        QMessageBox.information(self, 'Upload Overlay', 'Upload complete')
        try:
            os.remove(self.tmpArchiveFilePath)
        except:
            QMessageBox.warning(self, 'Upload Overlay', 'Failed to remove temporary file %s' % self.tmpArchiveFilePath)
        self.statusLabel.setText('')
        self.progressBar.setVisible(False)
        self.uploadPushButton.setText('Upload')
        self.uploadPushButton.setEnabled(True)
        self.updateDiskUsageBar()
        self.refreshOverlays()
        
    
    def lastFolder(self):

        # Retrieve the last place we looked if stored
        settings = QSettings()
        try:
            return settings.value("illuvisUpload/lastFolder").toString()
        except AttributeError:  # QGIS 2
            return settings.value("illuvisUpload/lastFolder")
    
    def browseForFile(self):
        currentPath = self.resultFileLineEdit.text()
        startingFolder = self.lastFolder()
        if os.path.isabs(currentPath):
            base, fName = os.path.split(currentPath)
            startingFolder = base
        
        inFileName = QFileDialog.getOpenFileName(self, \
                                                 'Select Result File', \
                                                 startingFolder, \
                                                 'GeoTIFF Files (*.tif)')
        
        # Store the path we just looked in
        head, tail = os.path.split(inFileName)
        if head <> os.sep and head.lower() <> 'c:\\' and head <> '':
            self.resultFileLineEdit.setText( unicode(inFileName) )
            settings = QSettings()
            settings.setValue("illuvisUpload/lastFolder", head)

    def newProjectPushButtonPressed(self):
        d = new_project_dialog.NewProjectDialog(self)
        d.show()
        res = d.exec_()
        if res == QDialog.Accepted:
            # The new project was created, refresh the project list
            self.ilCon.listProjects()
            
    def newOverlayPushButtonPressed(self):
        overlayData = {}
        d = new_overlay_dialog.NewOverlayDialog(self, overlayData)
        d.show()
        res = d.exec_()
        if res == QDialog.Accepted:
            # The user has opted to upload an overlay
            self.uploadOverlay(overlayData)
            
    def newScenarioPushButtonPressed(self):
        d = new_scenario_dialog.NewScenarioDialog(self, self.projectComboBox.currentIndex())
        d.show()
        res = d.exec_()
        if res == QDialog.Accepted:
            # The new scenario was created, refresh the scenario list
            self.refreshScenarios()
    
    def newEventPushButtonPressed(self):
        d = new_event_dialog.NewEventDialog(self, self.scenarioComboBox.currentIndex())
        d.show()
        res = d.exec_()
        if res == QDialog.Accepted:
            # The new event was created, refresh the event list
            self.refreshEvents()

    def deleteProjectPushButtonPressed(self):
        reply = QMessageBox.question(self, 'Delete Project?', \
                'WARNING: Deleting this project will permanently delete all its associated scenarios, events and map data. Are you sure you wish to proceed?', \
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            self.ilCon.deleteProject( self.projectComboBox.currentIndex() )
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Delete Project', 'The following error occured when deleting the project: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Delete Project', 'The following unexpected error occured when deleting the project: %s' % traceback.format_exc())
        self.refreshProjects()
        self.updateDiskUsageBar()
    
    def deleteScenarioPushButtonPressed(self):
        reply = QMessageBox.question(self, 'Delete Scenario?', \
                'WARNING: Deleting this scenario will permanently delete all its associated events and map data. Are you sure you wish to proceed?', \
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            self.ilCon.deleteScenario( self.scenarioComboBox.currentIndex() )
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Delete Scenario', 'The following error occured when deleting the scenario: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Delete Scenario', 'The following unexpected error occured when deleting the scenario: %s' % traceback.format_exc())
        self.refreshScenarios()
        self.updateDiskUsageBar()
    
    def deleteEventPushButtonPressed(self):
        reply = QMessageBox.question(self, 'Delete Event?', \
                'WARNING: Deleting this event will permanently delete all its associated map data. Are you sure you wish to proceed?', \
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            self.ilCon.deleteEvent( self.eventComboBox.currentIndex() )
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Delete Event', 'The following error occured when deleting the event: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Delete Event', 'The following unexpected error occured when deleting the event: %s' % traceback.format_exc())
        self.refreshEvents()
        self.updateDiskUsageBar()
        
    def deleteOverlayPushButtonPressed(self):
        reply = QMessageBox.question(self, 'Delete Overlay?', \
                'WARNING: Overlay will be permanently deleted. Are you sure you wish to proceed?', \
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            self.ilCon.deleteOverlay( self.overlayComboBox.currentIndex() )
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Delete Overlay', 'The following error occured when deleting the overlay: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Delete Overlay', 'The following unexpected error occured when deleting the overlay: %s' % traceback.format_exc())
        self.refreshOverlays()
        self.updateDiskUsageBar()
        
    def helpPressed(self):
        QDesktopServices.openUrl(QUrl('https://www.illuvis.com/docs/uploading'))

    def openLink(self, link):
        QDesktopServices.openUrl(QUrl(link))


    def updateResultSourceGUI(self):
        hasEvents = self.eventComboBox.count() > 0
        fromCurrent = self.fromCurrentRadioButton.isChecked()
        self.resolutionSpinBox.setEnabled(hasEvents and fromCurrent)
        self.resultFileLineEdit.setEnabled(hasEvents and not fromCurrent)
        self.browsePushButton.setEnabled(hasEvents and not fromCurrent)
