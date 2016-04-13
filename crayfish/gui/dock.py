# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
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

from ..core import DataSet, DS_Bed, DS_Vector
from .plot_widget import CrayfishPlotWidget
from .vector_options_dialog import CrayfishVectorOptionsDialog
from .mesh_options_dialog import CrayfishMeshOptionsDialog
from .render_settings import CrayfishRenderSettings
from .utils import load_ui, initColorButton, initColorRampComboBox, name2ramp, time_to_string
from .dataset_view import DataSetModel
from .colormap_dialog import CrayfishColorMapDialog

uiDialog, qtBaseClass = load_ui('crayfish_viewer_dock_widget')

class CrayfishDock(qtBaseClass, uiDialog):

    def __init__(self, iface):

        qtBaseClass.__init__(self)
        uiDialog.__init__(self)

        self.setupUi(self)
        self.setObjectName("CrayfishViewerDock") # used by main window to save/restore state
        self.iface = iface

        self.addIlluvisPromo()

        self.plot_dock_widget = None

        # make sure we accept only doubles for min/max values
        self.contourMinLineEdit.setValidator(QDoubleValidator(self.contourMinLineEdit))
        self.contourMaxLineEdit.setValidator(QDoubleValidator(self.contourMaxLineEdit))

        initColorRampComboBox(self.cboContourBasic)

        iconOptions = QgsApplication.getThemeIcon( "/mActionOptions.svg" )
        self.btnAdvanced.setIcon(iconOptions)
        self.btnVectorOptions.setIcon(iconOptions)
        self.btnMeshOptions.setIcon(iconOptions)

        self.btnPlot.setIcon(QgsApplication.getThemeIcon("/histogram.png"))
        self.btnLockCurrent.setIcon(QgsApplication.getThemeIcon("/locked.svg"))

        self.setEnabled(False)
        self.vectorPropsDialog = None
        self.advancedColorMapDialog = None
        self.meshPropsDialog = None

        # Ensure refresh() is called when the layer changes
        QObject.connect(self.cboTime, SIGNAL("currentIndexChanged(int)"), self.outputTimeChanged)
        QObject.connect(self.sliderTime, SIGNAL("valueChanged(int)"), self.cboTime.setCurrentIndex)
        QObject.connect(self.btnFirst, SIGNAL("clicked()"), self.timeFirst)
        QObject.connect(self.btnPrev, SIGNAL("clicked()"), self.timePrev)
        QObject.connect(self.btnNext, SIGNAL("clicked()"), self.timeNext)
        QObject.connect(self.btnLast, SIGNAL("clicked()"), self.timeLast)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.currentLayerChanged)
        QObject.connect(self.contourCustomRangeCheckBox, SIGNAL("toggled(bool)"), self.contourCustomRangeToggled)
        QObject.connect(self.contourMinLineEdit, SIGNAL('textEdited(QString)'), self.contourRangeChanged)
        QObject.connect(self.contourMaxLineEdit, SIGNAL('textEdited(QString)'), self.contourRangeChanged)
        QObject.connect(self.contoursGroupBox, SIGNAL('toggled(bool)'), self.displayContoursButtonToggled)
        QObject.connect(self.contourTransparencySlider, SIGNAL('valueChanged(int)'), self.transparencyChanged)
        QObject.connect(self.cboContourBasic, SIGNAL('currentIndexChanged(int)'), self.contourColorMapChanged)
        QObject.connect(self.btnAdvanced, SIGNAL("clicked()"), self.editAdvanced)
        QObject.connect(self.radContourBasic, SIGNAL("clicked()"), self.setContourType)
        QObject.connect(self.radContourAdvanced, SIGNAL("clicked()"), self.setContourType)
        QObject.connect(self.btnMeshOptions, SIGNAL("clicked()"), self.displayMeshPropsDialog)
        QObject.connect(self.btnLockCurrent, SIGNAL("clicked()"), self.toggleLockCurrent)
        QObject.connect(self.btnPlot, SIGNAL("clicked()"), self.plot)
        self.treeDataSets.contourClicked.connect(self.datasetContourClicked)
        self.treeDataSets.vectorClicked.connect(self.datasetVectorClicked)


    def currentCrayfishLayer(self):
        """ return currently selected crayfish layer or None if there is no selection (of non-crayfish layer is current) """
        l = self.iface.mapCanvas().currentLayer()
        if l and l.type() == QgsMapLayer.PluginLayer and str(l.pluginLayerType()) == 'crayfish_viewer':
            return l

    def currentDataSet(self):
        l = self.currentCrayfishLayer()
        return l.currentDataSet() if l else None


    def displayVectorPropsDialog(self):
        if self.vectorPropsDialog is not None:
            self.vectorPropsDialog.close()

        rs = CrayfishRenderSettings( self.currentDataSet() )
        self.vectorPropsDialog = CrayfishVectorOptionsDialog(self.iface, rs, self.redrawCurrentLayer, self)
        self.vectorPropsDialog.show()


    def displayContoursButtonToggled(self, newState):
        """
            displayContoursCheckBox has been toggled
        """
        self.datasetContourClicked(self.currentCrayfishLayer().current_ds_index)


    def displayVectorsButtonToggled(self, newState):
        """
            displayVectorsCheckBox has been toggled
        """
        self.datasetVectorClicked(self.currentCrayfishLayer().current_ds_index)


    def displayMeshButtonToggled(self, newState):
        """
            displayMeshCheckBox has been toggled
        """

        self.btnMeshOptions.setEnabled(newState)

        l = self.iface.mapCanvas().currentLayer()
        l.config["mesh"] = newState
        self.redrawCurrentLayer()


    def displayMeshPropsDialog(self):
        if self.meshPropsDialog is not None:
            self.meshPropsDialog.close()

        if self.currentCrayfishLayer():
            self.meshPropsDialog = CrayfishMeshOptionsDialog(self.currentCrayfishLayer(), self.redrawCurrentLayer, self)
            self.meshPropsDialog.show()

    def contourCustomRangeToggled(self, on):
        """ set provider's custom range """

        ds = self.currentDataSet()

        ds.custom["c_basicCustomRange"] = on

        self.updateContourGUI(ds)

        self.updateColorMapAndRedraw(ds)


    def contourRangeChanged(self):
        """ set provider's custom range """
        ds = self.currentDataSet()
        try:
            minContour = float( str(self.contourMinLineEdit.text()) )
            maxContour = float( str(self.contourMaxLineEdit.text()) )

            ds.custom["c_basicCustomRangeMin"] = minContour
            ds.custom["c_basicCustomRangeMax"] = maxContour

            self.updateColorMapAndRedraw(ds)

        except ValueError:
            pass


    def updateContourGUI(self, ds):
        """ update GUI from provider's range """
        ds = self.currentDataSet()
        isBasic = ds.custom["c_basic"]
        self.cboContourBasic.setEnabled(isBasic)
        self.contourCustomRangeCheckBox.setEnabled(isBasic)
        self.btnAdvanced.setEnabled(not isBasic)
        self.lblAdvancedPreview.setEnabled(not isBasic)

        manualRange = ds.custom["c_basicCustomRange"]
        zMin = ds.custom["c_basicCustomRangeMin"] if manualRange else ds.value_range()[0]
        zMax = ds.custom["c_basicCustomRangeMax"] if manualRange else ds.value_range()[1]
        self.contourMinLineEdit.setEnabled(isBasic and manualRange)
        self.contourMaxLineEdit.setEnabled(isBasic and manualRange)
        self.contourMinLineEdit.setText( str("%.3f" % zMin) )
        self.contourMaxLineEdit.setText( str("%.3f" % zMax) )


    def transparencyChanged(self, value):
        ds = self.currentDataSet()
        ds.custom["c_alpha"] = 255-value
        self.updateColorMapAndRedraw(ds)


    def dataSetChanged(self, index):

        dataSetItem = self.treeDataSets.model().index2item(index)
        if dataSetItem is None:
            return

        l = self.currentCrayfishLayer()
        if not l:
            return

        dataSet = l.mesh.dataset(dataSetItem.ds_index)
        old_ds_index = l.current_ds_index
        l.current_ds_index = dataSetItem.ds_index
        l.currentDataSetChanged.emit()  # let others know (e.g. plot widget)

        if l.lockCurrent:
            l.contour_ds_index = l.current_ds_index
            l.vector_ds_index = l.current_ds_index if dataSet.type() == DataSet.Vector else -1

        # repopulate the time control combo
        self.cboTime.blockSignals(True) # make sure that currentIndexChanged(int) will not be emitted
        self.cboTime.clear()
        if dataSet.time_varying():
            for output in dataSet.outputs():
                self.cboTime.addItem(time_to_string(output.time()))
        self.cboTime.blockSignals(False)

        self.sliderTime.setMaximum(dataSet.output_count()-1)

        # enable/disable time control depending on whether the data set is time varying
        for w in [self.cboTime, self.sliderTime, self.btnFirst, self.btnPrev, self.btnNext, self.btnLast]:
            w.setEnabled(dataSet.time_varying())

        # Restore the selection of the last time step that we viewed for this dataset
        if dataSet.time_varying():
            index = dataSet.output_time_index(l.current_output_time)
            if index is None:
                index = 0    # TODO: display some warning?
            self.cboTime.setCurrentIndex(index)

        # Get the contour settings from the provider

        rad = self.radContourBasic if dataSet.custom["c_basic"] else self.radContourAdvanced
        rad.blockSignals(True)
        rad.setChecked(True)
        rad.blockSignals(False)

        self.contourTransparencySlider.blockSignals(True)
        self.contourTransparencySlider.setValue( 255 - dataSet.custom["c_alpha"] )
        self.contourTransparencySlider.blockSignals(False)

        index = self.cboContourBasic.findText( dataSet.custom["c_basicName"] )
        self.cboContourBasic.blockSignals(True)
        self.cboContourBasic.setCurrentIndex(index)
        self.cboContourBasic.blockSignals(False)

        self.contourCustomRangeCheckBox.blockSignals(True)
        self.contourCustomRangeCheckBox.setChecked( dataSet.custom["c_basicCustomRange"] )
        self.contourCustomRangeCheckBox.blockSignals(False)

        self.updateContourGUI(dataSet)
        self.updateAdvancedPreview()
        self.updateDisplayContour()
        self.updateDisplayVector()

        # Disable the vector options if we are looking at a scalar dataset
        self.displayVectorsCheckBox.setEnabled(dataSet.type() == DS_Vector)

        self.iface.legendInterface().refreshLayerSymbology(l)

        self.redrawCurrentLayer()


    def outputTimeChanged(self, timeIdx):

        l = self.currentCrayfishLayer()
        if not l:
            return

        self.sliderTime.blockSignals(True)
        self.sliderTime.setValue(timeIdx)
        self.sliderTime.blockSignals(False)

        ds = l.currentDataSet()
        if ds.time_varying():
            l.current_output_time = ds.output(timeIdx).time()
            l.currentOutputTimeChanged.emit()   # let others know (e.g. plot widget)

        self.redrawCurrentLayer()

    def datasetContourClicked(self, ds_index):
        l = self.currentCrayfishLayer()
        if l.lockCurrent and ds_index != l.current_ds_index:
            return # operates on current dataset when locked

        if l.contour_ds_index == ds_index:
            l.contour_ds_index = -1   # toggle off
        else:
            l.contour_ds_index = ds_index

        self.updateDisplayContour()
        self.iface.legendInterface().refreshLayerSymbology(l)
        self.redrawCurrentLayer()

    def datasetVectorClicked(self, ds_index):
        l = self.currentCrayfishLayer()
        if l.lockCurrent and ds_index != l.current_ds_index:
            return # operates on current dataset when locked

        if l.vector_ds_index == ds_index:
            l.vector_ds_index = -1   # toggle off
        else:
            l.vector_ds_index = ds_index

        self.updateDisplayVector()
        self.iface.legendInterface().refreshLayerSymbology(l)
        self.redrawCurrentLayer()


    def updateDisplayContour(self):
        l = self.currentCrayfishLayer()
        self.treeDataSets.model().setActiveContourIndex(l.contour_ds_index)
        self.contoursGroupBox.blockSignals(True)
        self.contoursGroupBox.setChecked(l.contour_ds_index == l.current_ds_index)
        self.contoursGroupBox.blockSignals(False)

    def updateDisplayVector(self):
        l = self.currentCrayfishLayer()
        self.treeDataSets.model().setActiveVectorIndex(l.vector_ds_index)
        self.displayVectorsCheckBox.blockSignals(True)
        self.displayVectorsCheckBox.setChecked(l.vector_ds_index == l.current_ds_index)
        self.displayVectorsCheckBox.blockSignals(False)
        self.btnVectorOptions.setEnabled(l.vector_ds_index == l.current_ds_index)


    def deactivate(self):
        if not self.isEnabled():
            return
        QObject.disconnect(self.iface.mapCanvas(), SIGNAL("xyCoordinates(QgsPoint)"), self.reportValues)
        self.treeDataSets.setModel(None)
        self.cboTime.clear()
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

        dataSetItem = self.treeDataSets.model().index2item(self.treeDataSets.currentIndex())

        currentDs = dataSetItem.ds_index
        currentTs = self.cboTime.currentIndex()

        bed = l.mesh.dataset(0).output(0)
        bedValue = l.mesh.value(bed, xCoord, yCoord) # Note that the bed will always be 0, 0

        if bedValue == nullValue:
            # The mouse cursor is outside the mesh, exit nicely
            self.valueLabel.setText( '' )
            return

        textValue = str( '(%.3f)' % bedValue )

        dataSet = l.currentDataSet()
        if dataSet.type() != DS_Bed:
            # We're looking at an actual dataset rather than just the bed level
            dsValue = l.mesh.value(l.currentOutput(), xCoord, yCoord)
            if dsValue != nullValue:
                textValue += str(' %.3f' % dsValue)

        self.valueLabel.setText( textValue )


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

        self.updateLockCurrentIcon()

        # create new model with datasets
        datasets = []
        for i,d in enumerate(l.mesh.datasets()):
            datasets.append( (d.name(), d.type()) )
        self.treeDataSets.setModel(DataSetModel(datasets, l.ds_user_names))
        self.treeDataSets.selectionModel().currentRowChanged.connect(self.dataSetChanged)
        self.treeDataSets.model().setActiveContourIndex(l.contour_ds_index)
        self.treeDataSets.model().setActiveVectorIndex(l.vector_ds_index)
        self.treeDataSets.expandAll()

        # setup current dataset
        item = self.treeDataSets.model().datasetIndex2item(l.current_ds_index)
        if item:
            self.treeDataSets.setCurrentIndex( self.treeDataSets.model().item2index(item) )

        self.displayMeshCheckBox.blockSignals(True)
        self.displayMeshCheckBox.setChecked(l.config["mesh"])
        self.btnMeshOptions.setEnabled(l.config["mesh"])
        self.displayMeshCheckBox.blockSignals(False)

        #self.redrawCurrentLayer()


    def redrawCurrentLayer(self):
        l = self.currentCrayfishLayer()
        if l is None:
            return
        if hasattr(l, "setCacheImage"):
            l.setCacheImage(None)
        l.dataChanged.emit()  # profile tool may use this signal to update itself
        self.iface.mapCanvas().refresh()

    def contourColorMapChanged(self, idx):
        ds = self.currentDataSet()
        rampName = self.cboContourBasic.currentText()
        ramp = name2ramp(rampName)

        ds.custom["c_basicName"] = rampName
        ds.custom["c_basicRamp"] = ramp
        self.updateColorMapAndRedraw(ds)

    def updateColorMapAndRedraw(self, ds):
        self.iface.mapCanvas().currentLayer().updateColorMap(ds)
        if not ds.custom["c_basic"]:
            self.updateAdvancedPreview()
        self.redrawCurrentLayer()


    def editAdvanced(self):

        if self.advancedColorMapDialog is not None:
          self.advancedColorMapDialog.close()

        ds = self.currentDataSet()
        colormap = ds.custom["c_advancedColorMap"]

        zmin, zmax = ds.value_range()
        self.advancedColorMapDialog = CrayfishColorMapDialog(colormap, zmin, zmax, lambda: self.updateColorMapAndRedraw(ds), self)
        self.advancedColorMapDialog.show()
        self.updateColorMapAndRedraw(ds)


    def setContourType(self):
        ds = self.currentDataSet()
        basic = self.radContourBasic.isChecked()
        ds.custom["c_basic"] = basic

        self.updateContourGUI(ds)

        self.updateColorMapAndRedraw(ds)


    def updateAdvancedPreview(self):
        ds = self.currentDataSet()
        cm = ds.custom["c_advancedColorMap"]
        vMin,vMax = ds.value_range()
        pix = cm.previewPixmap(self.lblAdvancedPreview.size(), vMin, vMax)
        self.lblAdvancedPreview.setPixmap(pix)


    def addIlluvisPromo(self):

        if QSettings().value("/crayfishViewer/hideIlluvisPromo"):
          return

        self.labelPromo = QLabel(self)
        self.labelPromo.setStyleSheet("QLabel { background-color: #e7f5fe; border: 1px solid #b9cfe4; }")
        self.labelPromo.setWordWrap(True)
        self.labelPromo.setObjectName("labelPromo")
        self.labelPromo.setText(
          "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
          "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
          "p, li { white-space: pre-wrap; }\n"
          "</style></head><body><table<tr><td><span style=\" font-weight:600;\">Publish to the Web</span>"
          " - new integration with <span style=\" font-style:italic;\">illuvis</span> allows you to easily"
          " and securely share flood maps with colleagues, clients and other stakeholders. "
          "<a href=\"https://www.illuvis.com/?referrer=crayfish\">"
          "<span style=\" text-decoration: underline; color:#0057ae;\">Find out more</span></a></p></td>"
          "<td><a href=\"crayfish:closePromo\"><span style=\"text-decoration: none; color: #0057ae; font-weight:600;\">x</span></a>"
          "</td></tr></table></body></html>")
        self.labelPromo.linkActivated.connect(self.promoLinkActivated)
        self.verticalLayout_2.insertWidget(0, self.labelPromo)

    def promoLinkActivated(self, link):
        if link == "crayfish:closePromo":
          self.labelPromo.hide()
          QSettings().setValue("/crayfishViewer/hideIlluvisPromo", 1)
        elif link.startswith('http'):
          QDesktopServices.openUrl(QUrl(link))


    def timeFirst(self):
        self.cboTime.setCurrentIndex(0)

    def timePrev(self):
        idx = self.cboTime.currentIndex()-1
        if idx >= 0:
            self.cboTime.setCurrentIndex(idx)

    def timeNext(self):
        idx = self.cboTime.currentIndex()+1
        if idx < self.cboTime.count():
          self.cboTime.setCurrentIndex(idx)

    def timeLast(self):
        self.cboTime.setCurrentIndex(self.cboTime.count()-1)

    def toggleLockCurrent(self):
        l = self.iface.mapCanvas().currentLayer()
        l.lockCurrent = not l.lockCurrent
        self.updateLockCurrentIcon()

    def updateLockCurrentIcon(self):
        l = self.iface.mapCanvas().currentLayer()
        iconName = "/locked.svg" if l.lockCurrent else "/unlocked.svg"
        self.btnLockCurrent.setIcon(QgsApplication.getThemeIcon(iconName))

    def plot(self):
        if self.plot_dock_widget is None:
            self.plot_dock_widget = QDockWidget("Crayfish Plot")
            self.plot_dock_widget.setObjectName("CrayfishPlotDock")
            close_event = lambda event: self.btnPlot.setChecked(False) and QDockWidget.closeEvent(self.plot_dock_widget, event)
            self.plot_dock_widget.closeEvent = close_event
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock_widget)
            w = CrayfishPlotWidget(self.currentCrayfishLayer(), self.plot_dock_widget)
            self.plot_dock_widget.setWidget(w)
        else:
            self.plot_dock_widget.widget().set_layer(self.currentCrayfishLayer())
            self.plot_dock_widget.setVisible(not self.plot_dock_widget.isVisible())

        self.btnPlot.setChecked(self.plot_dock_widget.isVisible())
