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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from functools import partial
from .utils import load_ui, repopulate_time_control_combo

uiDialog, qtBaseClass = load_ui('crayfish_mesh_calculator_dialog')

ALLOWED_SUFFIX = ".dat"

class CrayfishMeshCalculatorDialog(qtBaseClass, uiDialog):

    def __init__(self, layer, parent=None):
        qtBaseClass.__init__(self)
        uiDialog.__init__(self, parent)

        self.setupUi(self)

        self.layer = layer

        self.insertAvailableDatasets()

        self.mDatasetsListWidget.itemDoubleClicked.connect(self.on_datasets_item_double_clicked)
        self.mOutputDatasetLineEdit.textChanged.connect(self.on_dataset_output_filename_changed)
        self.mOutputDatasetPushButton.clicked.connect(self.on_select_output_filename_clicked)

        self.mCurrentLayerExtentButton.clicked.connect(self.on_use_current_layer_extent_clicked)
        self.mAllTimesButton.clicked.connect(self.on_use_current_dataset_times_clicked)
        self.mDatasetsListWidget.itemSelectionChanged.connect(self.on_dataset_selected)

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
            (self.mMinButton, "min ("),
            (self.mMaxButton, "max ("),
            (self.mAbsButton, "abs ("),
            (self.mPowButton, "^"),
            (self.mIfButton, "if ("),
            (self.mAndButton, "and"),
            (self.mOrButton, "or"),
            (self.mNotButton, "not"),
            (self.mSumAggrButton, "sum_aggr ("),
            (self.mMaxAggrButton, "max_aggr ("),
            (self.mMinAggrButton, "min_aggr ("),
            (self.mAverageAggrButton, "average_aggr (")
        ]:
            btn.clicked.connect(partial(self.on_calc_button_clicked, text=text))

        self.set_full_extent()
        self.repopulate_time_combos()
        self.set_all_times()
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def formula_string(self):
        return self.mExpressionTextEdit.toPlainText()

    def expressionValid(self):
        if not self.formula_string():
            return False
        # Returns true if mesh calculator expression has valid syntax
        return self.layer.mesh.calc_expression_is_valid(self.formula_string())

    def time_filter(self):
        datasetName = self._dataset_name()
        dataset = self.layer.mesh.dataset_from_name(datasetName)
        start_time, end_time = dataset.time_range()

        if self.mStartTimeComboBox.currentIndex():
            min_t = max(start_time, self.mStartTimeComboBox.itemData(self.mStartTimeComboBox.currentIndex()))
        else:
            min_t = start_time

        if self.mEndTimeComboBox.currentIndex():
            max_t = min(end_time, self.mEndTimeComboBox.itemData(self.mEndTimeComboBox.currentIndex()))
        else:
            max_t = end_time
        return min_t, max_t

    def spatial_filter(self):
        layerExtent = self.layer.extent()
        self.mXMinSpinBox.value()
        self.mXMaxSpinBox.value()
        self.mYMinSpinBox.value()
        self.mYMaxSpinBox.value()

        return (
            max(self.mXMinSpinBox.value(), layerExtent.xMinimum()),
            max(self.mYMinSpinBox.value(), layerExtent.yMinimum()),
            min(self.mXMaxSpinBox.value(), layerExtent.xMaximum()),
            min(self.mYMaxSpinBox.value(), layerExtent.yMaximum())
        )

    def output_filename(self):
        outputFileName = self.mOutputDatasetLineEdit.text()
        if not outputFileName:
            return None

        return self._add_suffix(outputFileName)

    def filePathValid(self):
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
        self.setAcceptButtonState()

    def on_mButtonBox_accepted(self):
        self.layer.mesh.create_derived_dataset(
            expression=self.formula_string(),
            time_filter=self.time_filter(),
            spatial_filter=self.spatial_filter(),
            add_to_mesh=self.add_dataset_to_layer(),
            output_filename=self.output_filename()
        )

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

    def on_use_current_layer_extent_clicked(self):
        self.set_full_extent()

    def on_use_current_dataset_times_clicked(self):
        self.set_all_times()

    def on_mExpressionTextEdit_textChanged(self):
        if self.expressionValid():
            self.mExpressionValidLabel.setText("Expression Valid")
            if self.filePathValid():
                self.mButtonBox.button( QDialogButtonBox.Ok).setEnabled(True)
                return
        else:
            self.mExpressionValidLabel.setText("Expression invalid")
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def setAcceptButtonState(self):
        # Enables OK button if calculator expression is valid and output file path exists
        if self.expressionValid() and self.filePathValid():
            self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def add_dataset_to_layer(self):
        return self.mAddDatasetToLayerCheckBox.isChecked()

    def insertAvailableDatasets(self):
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
        datasetName = self._dataset_name()
        dataset = self.layer.mesh.dataset_from_name(datasetName)
        repopulate_time_control_combo(self.mStartTimeComboBox, dataset)
        repopulate_time_control_combo(self.mEndTimeComboBox, dataset)

    def set_all_times(self):
        datasetName = self._dataset_name()
        self._set_times_by_dataset_name(datasetName)

    def on_dataset_selected(self):
        self.repopulate_time_combos()

    def on_datasets_item_double_clicked(self, item): # QListWidgetItem
        self.on_calc_button_clicked(self.quoteBandEntry(item.text() ))

    def on_calc_button_clicked(self, text):
        self.mExpressionTextEdit.insertPlainText(" " + text + " ")

    def quoteBandEntry(self, datasetName):
        return '\"' + datasetName.replace('\"', "\\\"") + '\"'
