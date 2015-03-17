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

from new_event_dialog_widget import Ui_Dialog

class NewEventDialog(QDialog, Ui_Dialog):
    
    def __init__(self, parent, scenarioId):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.eventNameLineEdit.setFocus()
        self.parent = parent
        self.ilCon = parent.ilCon
        self.scenarioId = scenarioId
        self.existingEvents = []
        
        # Disconnect parent's slots
        self.ilCon.processedListEventsResponseSignal.disconnect(self.parent.handleRefreshEvents)
        self.ilCon.processedListEventsResponseSignal.connect(self.handleRefreshEvents)
        self.ilCon.requestFailedSignal.disconnect(self.parent.reportError)
        self.ilCon.requestFailedSignal.connect(self.reportError)
        
        self.ilCon.listEvents(scenarioId)
        
    def __del__(self):
        # Restore connections
        self.ilCon.requestFailedSignal.disconnect(self.reportError)
        self.ilCon.requestFailedSignal.connect(self.parent.reportError)
        self.ilCon.processedListEventsResponseSignal.disconnect(self.handleRefreshEvents)
        self.ilCon.processedListEventsResponseSignal.connect(self.parent.handleRefreshEvents)
            
    def reportError(self, msg):
        QMessageBox.critical(self, 'Illuvis Request Failed', msg)
    
    def handleRefreshEvents(self, events):
        # Populate te list of other events and optionally enable the 
        # controls
        for event in events:
            self.eventNamesComboBox.addItem(event['name'])
            self.existingEvents.append(event)
        if self.eventNamesComboBox.count() > 0:
            self.eventNamesComboBox.setEnabled(True)
            self.copyPushButton.setEnabled(True)
            
    def create(self):
        eventName = self.eventNameLineEdit.text()
        climateChange = self.climateChangeCheckBox.isChecked()
        additionalParams = {}
        if len(self.returnPeriodLineEdit.text()) > 0:
            additionalParams['return_period'] = self.returnPeriodLineEdit.text()
        if len(self.stormDurationLineEdit.text()) > 0:
            additionalParams['storm_duration'] = self.stormDurationLineEdit.text()
        if len(self.modellerLineEdit.text()) > 0:
            additionalParams['modeller'] = self.modellerLineEdit.text()
        if len(self.modelNameLineEdit.text()) > 0:
            additionalParams['model_name'] = self.modelNameLineEdit.text()
        if len(self.modelVersionLineEdit.text()) > 0:
            additionalParams['model_version'] = self.modelVersionLineEdit.text()
        if len(self.descriptionTextEdit.toPlainText()) > 0:
            additionalParams['description'] = self.descriptionTextEdit.toPlainText()
        
        try:
            self.ilCon.createEvent(self.scenarioId, eventName, climateChange, **additionalParams)
            self.accept()
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Create Event', 'The following error occured when creating the event: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Create Event', 'The following unexpected error occured when creating the event: %s' % traceback.format_exc())
    
    
    def copyButtonPressed(self):
        selectedIdx = self.eventNamesComboBox.currentIndex()
        donorEvent = self.existingEvents[selectedIdx]
        
        self.eventNameLineEdit.setText( donorEvent['name'] )
        self.returnPeriodLineEdit.setText( donorEvent.get('return_period', '') )
        self.stormDurationLineEdit.setText( donorEvent.get('storm_duration', '') )
        self.modellerLineEdit.setText( donorEvent.get('modeller', '') )
        self.modelNameLineEdit.setText( donorEvent.get('model_name', '') )
        self.modelVersionLineEdit.setText( donorEvent.get('model_version', '') )
        if donorEvent['climate_change'] == 'true':
            self.climateChangeCheckBox.setChecked( True )
        else:
            self.climateChangeCheckBox.setChecked( False )
        self.descriptionTextEdit.setDocument(QTextDocument( donorEvent.get('description', '') ))
        
    
    def helpPressed(self):
        QDesktopServices.openUrl(QUrl('https://www.illuvis.com/docs/events#qgis-create-event'))
