# -*- coding: utf-8 -*-

# illuvis - Tools for the effective communication of flood risk
# Copyright (C) 2013 Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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

from new_overlay_dialog_widget import Ui_Dialog

class NewOverlayDialog(QDialog, Ui_Dialog):
    
    def __init__(self, parent, overlayData):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        
        self.overlayData = overlayData
        self.registry = QgsMapLayerRegistry.instance()
        for lid, layer in self.registry.mapLayers().iteritems():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.layerComboBox.addItem(layer.name())
        
        if self.layerComboBox.count() > 1:
            self.layerComboBox.setEnabled(True)
            self.overlayNameLineEdit.setEnabled(True)
        self.layerComboBox.setFocus()
        self.parent = parent
        self.ilCon = parent.ilCon
    
    def firstLayerFromName(self, name):
        for lid, layer in self.registry.mapLayers().iteritems():
            if layer.name() == name:
                return layer
        return None
    
    def refreshColumns(self):
        while self.columnForLabelsComboBox.count() > 1:
            self.columnForLabelsComboBox.removeItem(1)
        if self.layerComboBox.currentIndex() == 0:
            return
        lay = self.firstLayerFromName(self.layerComboBox.currentText())
        if lay is None:
            return
        for fName, fId in lay.dataProvider().fieldNameMap().iteritems():
            self.columnForLabelsComboBox.addItem(fName)
        if self.columnForLabelsComboBox.count() > 1:
            self.columnForLabelsComboBox.setEnabled(True)
        else:
            self.columnForLabelsComboBox.setEnabled(False)
    
    def create(self):
        
        # Check a layer has been selected
        if self.layerComboBox.currentIndex() == 0:
            QMessageBox.critical(self, 'Upload Overlay', 'Please select a vector layer.')
            return
        
        # Check that layer is not editable (promt to go ahead)
        selectedLayer = self.firstLayerFromName( self.layerComboBox.currentText() )
        if selectedLayer.isModified():
            reply = QMessageBox.question(self, 'Unsaved Changes in Layer', \
                'WARNING: The selected layer has unsaved changes which will not be uploaded. Do you wish to proceed anyway?', \
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            
        # Check that layer has at least one feature
        if selectedLayer.featureCount() == 0:
            QMessageBox.critical(self, 'Upload Overlay', 'Please select a vector layer containing at least one feature.')
            return
        
        # Check selected layer is a shapefile
        if selectedLayer.dataProvider().storageType() != 'ESRI Shapefile':
            QMessageBox.critical(self, 'Upload Overlay', 'Only shapefiles are supported as overlays at this time.')
            return
        
        # Check an overlay name has been given
        if len( self.overlayNameLineEdit.text() ) == 0:
            QMessageBox.critical(self, 'Upload Overlay', 'Please enter a name for the overlay.')
            return
        
        # Update self.overlayData and accept() the dialog
        self.overlayData['layer'] = selectedLayer
        if self.columnForLabelsComboBox.currentIndex() != 0:
            self.overlayData['label_column'] = self.columnForLabelsComboBox.currentText()
        self.overlayData['name'] = self.overlayNameLineEdit.text()
        self.accept()
    
    
    def helpPressed(self):
        QDesktopServices.openUrl(QUrl('https://www.illuvis.com/docs/overlays#qgis-upload-overlays'))
