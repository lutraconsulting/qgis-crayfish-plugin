# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2017 Lutra Consulting

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

import os
from collections import OrderedDict
from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis._core import QgsVectorLayer, QGis, QgsMapLayer, QgsMapLayerRegistry

from .utils import load_ui, time_to_string

uiDialog, qtBaseClass = load_ui('crayfish_mesh_calculator_dialog')

ALLOWED_SUFFIX = ".dat"


class CrayfishMeshCalculatorDialog(qtBaseClass, uiDialog):
    dataset_added = pyqtSignal(object)  # layer

    def __init__(self, layer, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)

        self.layer = layer

        self.insert_available_datasets()

        self.mDatasetsListWidget.itemDoubleClicked.connect(self.on_datasets_item_double_clicked)
        self.mOutputDatasetLineEdit.textChanged.connect(self.on_dataset_output_filename_changed)
        self.mOutputDatasetPushButton.clicked.connect(self.on_select_output_filename_clicked)
        self.mMaskLayerFileBtn.clicked.connect(self.on_select_mask_layer_clicked)

        self.mCurrentLayerExtentButton.clicked.connect(self.on_use_current_layer_extent_clicked)
        self.mAllTimesButton.clicked.connect(self.on_use_current_dataset_times_clicked)

        self.mExpressionTextEdit.textChanged.connect(self._on_expression_changed)
        self.mButtonBox.accepted.connect(self.on_accept_clicked)

        self.useMaskCb.stateChanged.connect(self.toogle_extend_mask)
        self.useExtentCb.stateChanged.connect(self.toogle_extend_mask)
        self.maskBox.setVisible(False)

        for btn, text in [
            (self.mPlusPushButton, "+"),
            (self.mMinusPushButton, "-"),
            (self.mLessButton, "<"),
            (self.mLesserEqualButton, "<="),
            (self.mMultiplyPushButton, "*"),
            (self.mDividePushButton, "/"),
            (self.mGreaterButton, ">"),
            (self.mGreaterEqualButton, ">="),
            (self.mOpenBracketPushButton, "("),
            (self.mCloseBracketPushButton, ")"),
            (self.mEqualButton, "="),
            (self.mNotEqualButton, "!="),
            (self.mMinButton, "min ( A , B )"),
            (self.mMaxButton, "max ( A , B )"),
            (self.mAbsButton, "abs ("),
            (self.mPowButton, "^"),
            (self.mIfButton, "if ( 1 = 1 , NODATA , NODATA )"),
            (self.mAndButton, "and"),
            (self.mOrButton, "or"),
            (self.mNotButton, "not"),
            (self.mSumAggrButton, "sum_aggr ("),
            (self.mMaxAggrButton, "max_aggr ("),
            (self.mMinAggrButton, "min_aggr ("),
            (self.mAverageAggrButton, "average_aggr ("),
            (self.mNoDataButton, "NODATA")
        ]:
            btn.clicked.connect(partial(self.on_calc_button_clicked, text=text))

        self.set_full_extent()
        self.repopulate_time_combos()
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def formula_string(self):
        return self.mExpressionTextEdit.toPlainText()

    def expression_valid(self):
        if not self.formula_string():
            return False
        # Returns true if mesh calculator expression has valid syntax
        return self.layer.mesh.calc_expression_is_valid(self.formula_string())

    def time_filter(self):
        if self.mStartTimeComboBox.currentIndex() > -1:
            min_t = self.mStartTimeComboBox.itemData(self.mStartTimeComboBox.currentIndex())
        else:
            min_t = None

        if self.mEndTimeComboBox.currentIndex() > -1:
            max_t = self.mEndTimeComboBox.itemData(self.mEndTimeComboBox.currentIndex())
        else:
            max_t = None
        return min_t, max_t

    def spatial_filter(self):
        return (
            self.mXMinSpinBox.value(),
            self.mXMaxSpinBox.value(),
            self.mYMinSpinBox.value(),
            self.mYMaxSpinBox.value()
        )

    def output_filename(self):
        output_file_name = self.mOutputDatasetLineEdit.text()
        if not output_file_name:
            return None

        return self._add_suffix(output_file_name)

    def file_path_valid(self):
        outputPath = self.mOutputDatasetLineEdit.text()
        if not outputPath:
            return False

        outputPath = QFileInfo(outputPath).absolutePath()
        return QFileInfo(outputPath).isWritable()

    def _add_suffix(self, filename):
        if filename.endswith(ALLOWED_SUFFIX):
            return filename

        return filename + ALLOWED_SUFFIX

    def add_dataset_to_layer(self):
        return self.mAddDatasetToLayerCheckBox.isChecked()

    def on_dataset_output_filename_changed(self, dummy):
        self.set_accept_button_state()

    def list_polygon_layers(self):
        return [layer for layer in QgsMapLayerRegistry.instance().mapLayers().values() if
                layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon]

    def combine_geometries(self, features):
        geoms = None
        for feat in features:
            geom = feat.geometry()
            if not geom: continue

            err = geom.validateGeometry()
            if not err:
                if not geoms:
                    geoms = geom
                else:
                    geoms = geoms.combine(geom)
            else:
                pass

        return geoms

    def toogle_extend_mask(self):
        if self.useMaskCb.checkState() == Qt.Checked:
            self.extendBox.setVisible(False)
            self.maskBox.setVisible(True)
        else:
            self.extendBox.setVisible(True)
            self.maskBox.setVisible(False)

    def on_accept_clicked(self):
        mesh = self.layer.mesh

        success = None
        if self.useMaskCb.checkState() == Qt.Checked:
            mask_layer = self.cboLayerMask.currentLayer()
            feats = list(mask_layer.getFeatures())
            if mask_layer and feats:
                geoms = self.combine_geometries(feats)
                success = mesh.create_derived_dataset_mask(
                    expression=self.formula_string(),
                    time_filter=self.time_filter(),
                    geom_wkt=geoms.exportToWkt(),
                    add_to_mesh=self.add_dataset_to_layer(),
                    output_filename=self.output_filename())

        else:
            success = mesh.create_derived_dataset(
                expression=self.formula_string(),
                time_filter=self.time_filter(),
                spatial_filter=self.spatial_filter(),
                add_to_mesh=self.add_dataset_to_layer(),
                output_filename=self.output_filename()
            )

        if success:
            QMessageBox.information(self,
                                    'Mesh Calculator',
                                    'New dataset created successfully {}'.format(self.output_filename()))
            if self.add_dataset_to_layer():
                new_dataset_index = mesh.dataset_count() - 1
                self.layer.initCustomValues(mesh.dataset(new_dataset_index))
                self.dataset_added.emit(self.layer)

        else:
            QMessageBox.critical(self,
                                 'Mesh Calculator',
                                 "Unable to calculate new dataset. \n" +
                                 "Please check the output location if writtable and" +
                                 " that expression references existing datasets")

        self.close()

    def on_select_output_filename_clicked(self):
        s = QSettings()
        lastDir = s.value("crayfish/MeshCalculator/lastOutputDir", os.getcwd())
        saveFileName = QFileDialog.getSaveFileName(self, "Enter result file", lastDir)
        if saveFileName:
            saveFileName = self._add_suffix(saveFileName)
            basedir = os.path.dirname(saveFileName)
            s = QSettings()
            s.setValue("crayfish/MeshCalculator/lastOutputDir", basedir)
            self.mOutputDatasetLineEdit.setText(saveFileName)

    def on_select_mask_layer_clicked(self):
        s = QSettings()
        lastDir = s.value("crayfish/MeshCalculator/maskDir", os.getcwd())
        file_name = QFileDialog.getOpenFileName(self, "Enter mask layer file", lastDir)
        if file_name:
            basedir = os.path.dirname(file_name)
            s = QSettings()
            s.setValue("crayfish/MeshCalculator/maskDir", basedir)

            loaded_layer = None
            try:
                loaded_layer = QgsVectorLayer(file_name, file_name, "ogr")
                QgsMapLayerRegistry.instance().addMapLayer(loaded_layer)
            except:
                QMessageBox.information(self, "Cannot load mask layer", "Mask layer file is not valid.")

            if loaded_layer and loaded_layer.isValid() and loaded_layer.geometryType() == QGis.Polygon:
                self.cboLayerMask.addItem(loaded_layer.name(), loaded_layer)
                self.cboLayerMask.setLayer(loaded_layer)
            else:
                QMessageBox.information(self, "Cannot load mask layer", "Mask layer file is not valid.")

    def on_use_current_layer_extent_clicked(self):
        self.set_full_extent()

    def on_use_current_dataset_times_clicked(self):
        self.set_all_times()

    def _on_expression_changed(self):
        if self.expression_valid():
            self.mExpressionValidLabel.setText("Expression Valid")
            if self.file_path_valid():
                self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(True)
                return
        else:
            self.mExpressionValidLabel.setText("Expression invalid")
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def set_accept_button_state(self):
        # Enables OK button if calculator expression is valid and output file path exists
        if self.expression_valid() and self.file_path_valid():
            self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def add_dataset_to_layer(self):
        return self.mAddDatasetToLayerCheckBox.isChecked()

    def insert_available_datasets(self):
        mesh = self.layer.mesh
        for dataset in mesh.datasets():
            self.mDatasetsListWidget.addItem(dataset.name())

    def set_full_extent(self):
        layerExtent = self.layer.extent()
        self.mXMinSpinBox.setValue(layerExtent.xMinimum())
        self.mXMaxSpinBox.setValue(layerExtent.xMaximum())
        self.mYMinSpinBox.setValue(layerExtent.yMinimum())
        self.mYMaxSpinBox.setValue(layerExtent.yMaximum())

    def _dataset_name(self):
        items = self.mDatasetsListWidget.selectedItems()
        if items:
            datasetName = items[0].text()
        else:
            datasetName = self.mDatasetsListWidget.item(0).text()
        return datasetName

    def _set_times_by_dataset_name(self, datasetName):
        dataset = self.layer.mesh.dataset_from_name(datasetName)
        if dataset:
            start_time, end_time = dataset.time_range()
            idx = self.mStartTimeComboBox.findData(start_time)
            if idx:
                self.mStartTimeComboBox.setCurrentIndex(idx)
            idx = self.mEndTimeComboBox.findData(end_time)
            if idx:
                self.mEndTimeComboBox.setCurrentIndex(idx)

    def repopulate_time_combos(self):
        times = {None: None}
        for dataSet in self.layer.mesh.datasets():
            for output in dataSet.outputs():
                str_time = time_to_string(output.time(), dataSet)
                times[str_time] = output.time()

        times = OrderedDict(sorted(times.items(), key=lambda t: t[1]))
        for cboTime in [self.mStartTimeComboBox, self.mEndTimeComboBox]:
            cboTime.blockSignals(True)  # make sure that currentIndexChanged(int) will not be emitted
            cboTime.clear()
            for str_time, time in times.iteritems():
                cboTime.addItem(str_time, time)
            cboTime.blockSignals(False)

        if len(times) > 1:
            self.mStartTimeComboBox.setCurrentIndex(1)
            self.mEndTimeComboBox.setCurrentIndex(len(times) - 1)

    def set_all_times(self):
        datasetName = self._dataset_name()
        self._set_times_by_dataset_name(datasetName)

    def on_datasets_item_double_clicked(self, item):  # QListWidgetItem
        self.on_calc_button_clicked(self.quote_band_entry(item.text()))

    def on_calc_button_clicked(self, text):
        self.mExpressionTextEdit.insertPlainText(" " + text + " ")

    def quote_band_entry(self, datasetName):
        return '\"' + datasetName.replace('\"', "\\\"") + '\"'
