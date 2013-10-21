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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_viewer_dock_widget import Ui_DockWidget
import crayfish_viewer_vector_options_dialog
from crayfish_viewer_render_settings import CrayfishViewerRenderSettings


class CrayfishViewerDock(QDockWidget, Ui_DockWidget):
    
    def __init__(self, iface):
        
        QDockWidget.__init__(self)
        Ui_DockWidget.__init__(self)
        
        self.setupUi(self)
        self.setObjectName("CrayfishViewerDock") # used by main window to save/restore state
        self.iface = iface
        
        # make sure we accept only doubles for min/max values
        self.contourMinLineEdit.setValidator(QDoubleValidator(self.contourMinLineEdit))
        self.contourMaxLineEdit.setValidator(QDoubleValidator(self.contourMaxLineEdit))

        self.setEnabled(False)
        self.vectorPropsDialog = None
        
        # Ensure refresh() is called when the layer changes
        QObject.connect(self.listWidget, SIGNAL("currentRowChanged(int)"), self.dataSetChanged)
        QObject.connect(self.listWidget_2, SIGNAL("currentRowChanged(int)"), self.outputTimeChanged)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.currentLayerChanged)
        QObject.connect(self.contourCustomRangeCheckBox, SIGNAL("toggled(bool)"), self.contourCustomRangeToggled)
        QObject.connect(self.contourMinLineEdit, SIGNAL('textEdited(QString)'), self.contourRangeChanged)
        QObject.connect(self.contourMaxLineEdit, SIGNAL('textEdited(QString)'), self.contourRangeChanged)
        QObject.connect(self.contoursGroupBox, SIGNAL('toggled(bool)'), self.displayContoursButtonToggled)
        QObject.connect(self.contourTransparencySlider, SIGNAL('valueChanged(int)'), self.transparencyChanged)
        
        
    def currentDataSet(self):
        l = self.iface.mapCanvas().currentLayer()
        return l.provider.dataSet( self.listWidget.currentRow() )
        
    def displayVectorPropsDialog(self):
        if self.vectorPropsDialog is not None:
            self.vectorPropsDialog.raise_()
            return
        rs = CrayfishViewerRenderSettings( self.currentDataSet() )
        self.vectorPropsDialog = crayfish_viewer_vector_options_dialog.CrayfishViewerVectorOptionsDialog(self.iface, rs, self.redrawCurrentLayer)
        self.vectorPropsDialog.show()
        res = self.vectorPropsDialog.exec_()
        self.redrawCurrentLayer()
        self.vectorPropsDialog = None

    
    def displayContoursButtonToggled(self, newState):
        """
            displayContoursCheckBox has been toggled
        """
        self.currentDataSet().setContourRenderingEnabled(newState)
        self.redrawCurrentLayer()
            
            
    def displayVectorsButtonToggled(self, newState):
        """
            displayVectorsCheckBox has been toggled
        """
        self.currentDataSet().setVectorRenderingEnabled(newState)
        self.vectorOptionsPushButton.setEnabled(newState)
        self.redrawCurrentLayer()
        
    def displayMeshButtonToggled(self, newState):
        """
            displayMeshCheckBox has been toggled
        """
        l = self.iface.mapCanvas().currentLayer()
        l.provider.setMeshRenderingEnabled(newState)
        self.redrawCurrentLayer()


    def contourCustomRangeToggled(self, on):
        """ set provider's auto range """

        ds = self.currentDataSet()
        ds.setContourAutoRange(not on)

        self.updateContourRange(ds)

        self.redrawCurrentLayer()


    def contourRangeChanged(self):
        """ set provider's custom range """
        ds = self.currentDataSet()
        try:
            minContour = float( str(self.contourMinLineEdit.text()) )
            maxContour = float( str(self.contourMaxLineEdit.text()) )
            ds.setContourCustomRange(minContour, maxContour)
            self.redrawCurrentLayer()
        except ValueError:
            pass


    def updateContourRange(self, dataSet):
        """ update GUI from provider's range """
        manualRange = not dataSet.contourAutoRange()
        zMin = dataSet.contourCustomRangeMin() if manualRange else dataSet.minZValue()
        zMax = dataSet.contourCustomRangeMax() if manualRange else dataSet.maxZValue()
        self.contourMinLineEdit.setEnabled(manualRange)
        self.contourMaxLineEdit.setEnabled(manualRange)
        self.contourMinLineEdit.setText( str("%.3f" % zMin) )
        self.contourMaxLineEdit.setText( str("%.3f" % zMax) )

        
    def transparencyChanged(self, value):
        self.currentDataSet().setContourAlpha(255-value)
        self.redrawCurrentLayer()
    
        
    def timeToString(self, hours):

        seconds = round(hours * 3600.0, 2)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return "%3d %02d:%02d:%05.2f" % (d, h, m, s)

        
    def dataSetChanged(self, dataSetRow):
        
        if dataSetRow < 0:
            return
        
        l = self.currentCrayfishLayer()
        if not l:
            return
          
        dataSet = l.provider.dataSet(dataSetRow)
        
        dataSetIdx = self.listWidget.currentRow()
        l.provider.setCurrentDataSetIndex(dataSetIdx)

        self.listWidget_2.blockSignals(True) # make sure that currentRowChanged(int) will not be emitted
        self.listWidget_2.clear()
        self.listWidget_2.blockSignals(False)

        if dataSet.isTimeVarying():
            self.listWidget_2.setEnabled(True)
            for i in range( dataSet.outputCount() ):
                t = dataSet.output(i).time
                timeString = self.timeToString(t)
                self.listWidget_2.addItem(timeString)
            # Restore the selection of the last time step that we viewed
            # for this dataset
            timeIdx = dataSet.currentOutputTime()
            self.listWidget_2.setCurrentRow(timeIdx)
        else:
            self.listWidget_2.setEnabled(False)
            
        # Get the contour settings from the provider
        self.contourTransparencySlider.blockSignals(True)
        self.contourTransparencySlider.setValue( 255 - dataSet.contourAlpha() )
        self.contourTransparencySlider.blockSignals(False)

        self.contourCustomRangeCheckBox.blockSignals(True)
        self.contourCustomRangeCheckBox.setChecked( not dataSet.contourAutoRange() )
        self.contourCustomRangeCheckBox.blockSignals(False)

        self.updateContourRange(dataSet)

            
        # Get contour / vector render preferences
        self.contoursGroupBox.setChecked(dataSet.isContourRenderingEnabled())
        self.displayVectorsCheckBox.setChecked(dataSet.isVectorRenderingEnabled())
        
        # Disable the vector options if we are looking at a scalar dataset
        from crayfishviewer import DataSetType
        self.displayVectorsCheckBox.setEnabled(dataSet.type() == DataSetType.Vector)
        
        self.redrawCurrentLayer()


    def outputTimeChanged(self, timeIdx):

        l = self.currentCrayfishLayer()
        if not l:
            return

        ds = l.provider.currentDataSet()
        ds.setCurrentOutputTime(timeIdx)

        self.redrawCurrentLayer()

        
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
        
        bed = l.provider.dataSet(0).output(0)
        bedValue = l.provider.valueAtCoord(bed, xCoord, yCoord) # Note that the bed will always be 0, 0
        
        if bedValue == nullValue:
            # The mouse cursor is outside the mesh, exit nicely
            self.valueLabel.setText( '' )
            return
            
        textValue = str( '(%.3f)' % bedValue )
        
        dataSet = self.currentDataSet()
        ts = dataSet.output(currentTs)
        from crayfishviewer import DataSetType
        if dataSet.type() != DataSetType.Bed:
            # We're looking at an actual dataset rather than just the bed level
            dsValue = l.provider.valueAtCoord(ts, xCoord, yCoord)
            if dsValue != nullValue:
                textValue += str(' %.3f' % dsValue)
        
        self.valueLabel.setText( textValue )
        
    def currentCrayfishLayer(self):
        """ return currently selected crayfish layer or None if there is no selection (of non-crayfish layer is current) """
        l = self.iface.mapCanvas().currentLayer()
        if l and l.type() == QgsMapLayer.PluginLayer and str(l.pluginLayerType()) == 'crayfish_viewer':
            return l


    def currentLayerChanged(self):
        """
            Refresh is usually called when the selected layer changes in the legend
            Refresh clears and repopulates the dock widgets, restoring them to their correct values
        """

        l = self.currentCrayfishLayer()
        if l is None:
            self.deactivate()
            return
                
        self.activate()

        # Clear everything
        self.listWidget.clear()

        # Add datasets
        for i in range(l.provider.dataSetCount()):
            n = l.provider.dataSet(i).name()
            self.listWidget.addItem(n)

        # setup current dataset
        dataSetIdx = l.provider.currentDataSetIndex()
        self.listWidget.setCurrentRow( dataSetIdx )

        self.displayMeshCheckBox.blockSignals(True)
        self.displayMeshCheckBox.setChecked(l.provider.isMeshRenderingEnabled())
        self.displayMeshCheckBox.blockSignals(False)

        #self.redrawCurrentLayer()


    def redrawCurrentLayer(self):
        l = self.currentCrayfishLayer()
        if l is None:
            return
        if hasattr(l, "setCacheImage"):
            l.setCacheImage(None)
        self.iface.mapCanvas().refresh()
