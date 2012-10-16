# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_viewer_dock_widget import Ui_DockWidget
import crayfish_viewer_vector_options_dialog

class CrayfishViewerDock(QDockWidget, Ui_DockWidget):
    
    def __init__(self, iface):
        
        QDockWidget.__init__(self)
        Ui_DockWidget.__init__(self)
        
        self.setupUi(self)
        self.iface = iface
        
        self.setEnabled(False)
        
        # Ensure refresh() is called when the layer changes
        QObject.connect(self.listWidget, SIGNAL("currentRowChanged(int)"), self.dataSetChanged)
        QObject.connect(self.listWidget_2, SIGNAL("currentRowChanged(int)"), self.redraw)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.refresh)
        QObject.connect(self.groupBox, SIGNAL("toggled(bool)"), self.toggleContourOptions)
        
        
    def __del__(self):
        # Disconnect signals and slots
        QObject.disconnect(self.groupBox, SIGNAL("toggled(bool)"), self.toggleContourOptions)
        QObject.disconnect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.refresh)
        QObject.disconnect(self.listWidget_2, SIGNAL("currentRowChanged(int)"), self.redraw)
        QObject.disconnect(self.listWidget, SIGNAL("currentRowChanged(int)"), self.dataSetChanged)
        
        
    def displayVectorPropsDialog(self):
        rs = self.iface.mapCanvas().currentLayer().rs
        d = crayfish_viewer_vector_options_dialog.CrayfishViewerVectorOptionsDialog(self.iface, rs, self.redrawCurrentLayer)
        d.show()
        res = d.exec_()
        self.redrawCurrentLayer()

    
    def displayContoursButtonToggled(self, newState):
        """
            displayContoursCheckBox has been toggled
        """
        l = self.iface.mapCanvas().currentLayer()
        if newState:
            #self.contourOptionsPushButton.setEnabled(True)
            l.rs.renderContours = True
        else:
            #self.contourOptionsPushButton.setEnabled(False)
            l.rs.renderContours = False
            # Ensure one or the other is on
            if not self.displayVectorsCheckBox.isEnabled():
                self.displayVectorsCheckBox.setCheckState(True)
                #self.displayVectorsCheckBox.toggled.emit(True)
        self.redrawCurrentLayer()
            
            
    def displayVectorsButtonToggled(self, newState):
        """
            displayVectorsCheckBox has been toggled
        """
        l = self.iface.mapCanvas().currentLayer()
        if newState:
            self.vectorOptionsPushButton.setEnabled(True)
            l.rs.renderVectors = True
        else:
            self.vectorOptionsPushButton.setEnabled(False)
            l.rs.renderVectors = False
            # Ensure one or the other is on
            if not self.displayContoursCheckBox.isEnabled():
                self.displayContoursCheckBox.setCheckState(True)
                #self.displayContoursCheckBox.toggled.emit(True)
        self.redrawCurrentLayer()
        
    
    def toggleContourOptions(self, on):
        if on:
            self.minLineEdit.setEnabled(True)
            self.maxLineEdit.setEnabled(True)
            l = self.iface.mapCanvas().currentLayer()
            dataSetRow = self.listWidget.currentRow()
            self.minLineEdit.setText( str("%.3f" % l.provider.lastMinContourValue(dataSetRow)) )
            self.maxLineEdit.setText( str("%.3f" % l.provider.lastMaxContourValue(dataSetRow)) )
        else:
            self.minLineEdit.setEnabled(False)
            self.maxLineEdit.setEnabled(False)
            l = self.iface.mapCanvas().currentLayer()
            dataSetRow = self.listWidget.currentRow()
            self.minLineEdit.setText( str("%.3f" % l.provider.minValue(dataSetRow)) )
            self.maxLineEdit.setText( str("%.3f" % l.provider.maxValue(dataSetRow)) )
    
    def showMostRecentDataSet(self):
        lastRow = self.listWidget.count() - 1
        # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Setting index to " + str(lastRow) )
        self.listWidget.setCurrentRow( lastRow )
        
    
    def redraw(self, timeIdx):
        l = self.iface.mapCanvas().currentLayer()
        if l is None:
            return
        if l.type() != QgsMapLayer.PluginLayer or str(l.pluginLayerType()) != 'crayfish_viewer':
            return
            
        dataSetIdx = self.listWidget.currentRow()
        l.setRenderSettings(dataSetIdx, timeIdx)
        l.setCacheImage(None)
            
        self.iface.mapCanvas().refresh()
        
    
        
    def timeToString(self, hours):
        
        seconds = hours * 3600.0
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return "%3d %02d:%02d:%05.2f" % (d, h, m, s)

        
    def dataSetChanged(self, dataSetRow):
        
        if dataSetRow < 0:
            return
        
        l = self.iface.mapCanvas().currentLayer()
        if l.type() != QgsMapLayer.PluginLayer or str(l.pluginLayerType()) != 'crayfish_viewer':
            return
        
        self.listWidget_2.clear()
        
        if l.provider.timeVarying(dataSetRow):
            self.listWidget_2.setEnabled(True)
            for i in range( l.provider.dataSetOutputCount(dataSetRow) ):
                t = l.provider.dataSetOutputTime(dataSetRow, i)
                timeString = self.timeToString(t)
                self.listWidget_2.addItem(timeString)
            # Restore the selection of the last time step that we viewed
            # for this dataset
            lastIdxViewed = l.provider.getLastRenderIndex(dataSetRow)
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Setting last time index to " + str(lastIdxViewed) )
            self.listWidget_2.setCurrentRow(lastIdxViewed)
        else:
            self.listWidget_2.setEnabled(False)
            
        # Get the contour settings from the provider
        contourAutomatically = l.provider.layerContouredAutomatically(dataSetRow)
        self.groupBox.setChecked( not contourAutomatically )
        if contourAutomatically:
            self.minLineEdit.setText( str("%.3f" % l.provider.minValue(dataSetRow)) )
            self.maxLineEdit.setText( str("%.3f" % l.provider.maxValue(dataSetRow)) )
        else:
            self.minLineEdit.setText( str("%.3f" % l.provider.lastMinContourValue(dataSetRow)) )
            self.maxLineEdit.setText( str("%.3f" % l.provider.lastMaxContourValue(dataSetRow)) )
        
    
    def getRenderOptions(self):
        autoRender = not self.groupBox.isChecked()
        minContour = float( str(self.minLineEdit.text()) )
        maxContour = float( str(self.maxLineEdit.text()) )
        return autoRender, minContour, maxContour
    
    
    def deactivate(self):
        if not self.isEnabled():
            return
        QObject.disconnect(self.iface.mapCanvas(), SIGNAL("xyCoordinates(QgsPoint)"), self.reportValues)
        self.listWidget.clear()
        self.listWidget_2.clear()
        self.valueLabel.setText( "" )
        self.setEnabled(False)
        
        
    def activate(self):
        """
            Activate should be called when an Crayfish layer is selected
            We also connect an event to the canvas here to report the 
            bed and quatity values
        """
        if self.isEnabled():
            return
        QObject.connect(self.iface.mapCanvas(), SIGNAL("xyCoordinates(QgsPoint)"), self.reportValues)
        self.setEnabled(True)
        
        
    def reportValues(self, p):
        
        nullValue = -9999.0
        
        xCoord = p.x()
        yCoord = p.y()
        
        l = self.iface.mapCanvas().currentLayer()
        
        currentDs = self.listWidget.currentRow()
        currentTs = self.listWidget_2.currentRow()
        
        bedValue = l.provider.valueAtCoord(0, 0, xCoord, yCoord) # Note that the bed will always be 0, 0
        
        if bedValue == nullValue:
            # The mouse cursor is outside the mesh, exit nicely
            self.valueLabel.setText( '' )
            return
            
        textValue = str( '(%.3f)' % bedValue )
            
        if not l.provider.isBed(currentDs):
            # We're looking at an actual dataset rather than just the bed level
            dsValue = l.provider.valueAtCoord(currentDs, currentTs, xCoord, yCoord)
            if dsValue != nullValue:
                textValue += str(' %.3f' % dsValue)
        
        self.valueLabel.setText( textValue )
        
    
    def refresh(self, l = None):
        """
            Refresh is usually called when the selected layer changes in the legend
            Refresh clears and repopulates the dock widgets, restoring them to their correct values
        """
        
        # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Refresh Called")
                
        if l is None:
            l = self.iface.mapCanvas().currentLayer()
            if l is None:
                self.deactivate()
                return
                
        if l.type() == QgsMapLayer.PluginLayer and str(l.pluginLayerType()) == 'crayfish_viewer':
            
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Activating")
            self.activate()
            
            # Clear everything
            self.listWidget.clear()
            
            # Add datasets
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Adding datasets in refresh()")
            for i in range(l.provider.dataSetCount()):
                n = l.provider.dataSetName(i)
                self.listWidget.addItem(n)
                
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Done adding datasets in refresh(), setting setCurrentRow")
                
            self.listWidget.setCurrentRow(0)
            
            # QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Done setting setCurrentRow")
                
        else:
            # disable the UI
            self.deactivate()
            
        self.redrawCurrentLayer()


    def redrawCurrentLayer(self):
        l = self.iface.mapCanvas().currentLayer()
        if hasattr(l, "setCacheImage"):
            l.setCacheImage(None)
        self.iface.mapCanvas().refresh()
        # l.triggerRepaint()
