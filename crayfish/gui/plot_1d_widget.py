# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2020 Lutra Consulting

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

import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *
from qgis.utils import iface

try:
    import pyqtgraph
except ImportError:
    import sys
    import os
    this_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(this_dir, os.pardir, 'pyqtgraph-0.10.0-py2.py3-none-any.whl')
    sys.path.append(path)
    import pyqtgraph

from ..plot import timeseries_plot_data, cross_section_plot_data, colors, profile_1D_plot_data
from .utils import time_to_string
from .plot_cf_layer_widget import CrayfishLayer1dWidget
from .plot_1d_profile_widget import Profile1DPickerWidget
from .plot_point_geometry_widget import PointGeometryPickerWidget
from .plot_datasets_widget import DatasetsWidget
from .plot_dataset_groups_widget import DatasetGroupsWidget
from .plot_map_layer_widget import MapLayersWidget


class Plot1dTypeMenu(QMenu):

    plot_type_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.names = ["Time series", "Longitudinal profile"]
        for i, plot_type_name in enumerate(self.names):
            a = self.addAction(plot_type_name)
            a.plot_type = i
            a.triggered.connect(self.on_action)

    def on_action(self):
        self.plot_type_changed.emit(self.sender().plot_type)


class PlotTypeWidget(QToolButton):

    plot_type_changed = pyqtSignal(int)

    PLOT_TIME, PLOT_LONG_PROFILE = range(2)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(QgsApplication.getThemeIcon("/histogram.png"))

        self.menu_plot_types = Plot1dTypeMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_plot_types)
        self.menu_plot_types.plot_type_changed.connect(self.on_plot_type_changed)
        self.set_plot_type(self.PLOT_TIME)

    def set_plot_type(self, plot_type):
        self.on_plot_type_changed(plot_type)

    def on_plot_type_changed(self, plot_type):
        self.plot_type = plot_type
        self.setText("Plot: " + self.menu_plot_types.names[self.plot_type])
        self.plot_type_changed.emit(plot_type)

class Plot1dPointGeometryPickerWidget(PointGeometryPickerWidget):

    def __init__(self, parent = None):
        PointGeometryPickerWidget.__init__(self,parent)
        self.meshLayer = None

    def on_picked(self, pt, clicked, with_ctrl):
        if self.meshLayer is None:
            return
        searchRadius=self.tool.searchRadiusMU(iface.mapCanvas())
        projectedPoint=self.meshLayer.snapOnElement(QgsMesh.Edge,pt,searchRadius)

        if projectedPoint.isEmpty():
            return

        super().on_picked(projectedPoint,clicked,with_ctrl)


class CrayfishPlot1dWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.layer = None

        self.btn_layer = CrayfishLayer1dWidget()
        self.btn_layer.layer_changed.connect(self.on_layer_changed)

        self.btn_dataset_group = DatasetGroupsWidget()
        self.btn_dataset_group.dataset_groups_changed.connect(self.on_dataset_group_changed)

        self.btn_plot_type = PlotTypeWidget()
        self.btn_plot_type.plot_type_changed.connect(self.on_plot_type_changed)

        self.btn_point_picker=QToolButton()
        self.btn_point_picker.setText("Select point from map")
        self.btn_point_picker.clicked.connect(self.on_point_button_clicked)

        self.point_picker = Plot1dPointGeometryPickerWidget()
        self.point_picker.geometries_changed.connect(self.refresh_plot)

        self.btn_from_pt_layer = MapLayersWidget(QgsWkbTypes.Point)
        self.btn_from_pt_layer.picked_layer.connect(self.point_picker.on_picked_layer)

        self.profile_picker = Profile1DPickerWidget()
        self.profile_picker.geometry_changed.connect(self.refresh_plot)

        self.chckBox_verticalLine=QCheckBox()
        self.chckBox_verticalLine.setText("Vertical lines on vertices")
        self.chckBox_verticalLine.setChecked(False)
        self.chckBox_verticalLine.toggled.connect(self.refresh_plot)

        self.btn_datasets = DatasetsWidget()
        self.btn_datasets.datasets_changed.connect(self.refresh_plot)

        self.markers = []      # for points

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()

        self.label_not_time_varying = QLabel("Current dataset group is not time-varying.")
        self.label_not_time_varying.setAlignment(Qt.AlignCenter)

        self.label_no_layer = QLabel("No mesh layer is selected.")
        self.label_no_layer.setAlignment(Qt.AlignCenter)

        self.stack_layout = QStackedLayout()
        self.stack_layout.addWidget(self.gw)
        self.stack_layout.addWidget(self.label_not_time_varying)
        self.stack_layout.addWidget(self.label_no_layer)

        hl = QHBoxLayout()
        hl.addWidget(self.btn_layer)
        hl.addWidget(self.btn_plot_type)
        hl.addWidget(self.btn_dataset_group)
        hl.addWidget(self.btn_datasets)
        hl.addWidget(self.point_picker)
        hl.addWidget(self.btn_point_picker)
        hl.addWidget(self.btn_from_pt_layer)
        hl.addWidget(self.profile_picker)
        hl.addStretch()
        hl.addWidget(self.chckBox_verticalLine)

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addLayout(self.stack_layout)
        self.setLayout(l)

        # init GUI
        self.on_plot_type_changed(self.btn_plot_type.plot_type)
        self.on_dataset_group_changed(self.btn_dataset_group.dataset_groups)

        iface.mapCanvas().temporalRangeChanged.connect(self.on_canvas_time_range_changed)

    def hideEvent(self, e):
        self.reset_widget()
        QWidget.hideEvent(self, e)

    def set_layer(self, layer):
        self.btn_layer.set_layer(layer)

    def on_layer_changed(self, layer):
        self.layer = layer
        self.btn_dataset_group.set_layer(layer)
        self.btn_datasets.set_layer(layer)
        self.profile_picker.initializeTracer(layer)
        self.point_picker.meshLayer=layer
        self.reset_widget()

    def on_plot_type_changed(self, plot_type):
        self.profile_picker.setVisible(plot_type == PlotTypeWidget.PLOT_LONG_PROFILE)
        self.btn_datasets.setVisible(plot_type == PlotTypeWidget.PLOT_LONG_PROFILE)
        self.btn_from_pt_layer.setVisible(plot_type == PlotTypeWidget.PLOT_TIME)
        self.btn_point_picker.setVisible(plot_type == PlotTypeWidget.PLOT_TIME)
        self.chckBox_verticalLine.setVisible(plot_type == PlotTypeWidget.PLOT_LONG_PROFILE)

        if plot_type == PlotTypeWidget.PLOT_LONG_PROFILE:
            self.point_picker.clear_geometries()
            self.point_picker.stop_picking()
        elif plot_type == PlotTypeWidget.PLOT_TIME:
            # if self.btn_from_pt_layer.picked_layer is None:
            self.point_picker.start_picking_map()
            self.profile_picker.clear_geometries()
            self.profile_picker.stop_picking()

        self.profile_picker.stop_picking()

        self.refresh_plot()

    def on_dataset_group_changed(self, lst):
        if len(lst) == 0:
            self.btn_datasets.set_dataset_group(self.layer.rendererSettings().activeScalarDatasetGroup() if self.layer is not None else None)
        elif len(lst) == 1:
            self.btn_datasets.set_dataset_group(lst[0])

        self.refresh_plot()

    def current_dataset_group(self):
        dataset_groups = self.btn_dataset_group.dataset_groups
        if len(dataset_groups) == 0:
          return self.layer.rendererSettings().activeScalarDatasetGroup() if self.layer is not None else None
        else:
          return dataset_groups[0]

    def on_canvas_time_range_changed(self):
        if len(self.btn_datasets.datasets) == 0:
            self.refresh_plot()

    def on_point_button_clicked(self):
        self.point_picker.picker_clicked()

    def reset_widget(self):
        self.point_picker.clear_geometries()
        self.point_picker.stop_picking()
        self.profile_picker.clear_geometries()
        self.profile_picker.stop_picking()
        self.refresh_plot()

    def refresh_plot(self):
        plot_type = self.btn_plot_type.plot_type

        if self.layer is None:
            self.stack_layout.setCurrentWidget(self.label_no_layer)
            return

        ds = self.current_dataset_group()
        if plot_type == PlotTypeWidget.PLOT_TIME and self.dataset_group_is_not_time_varying(ds):
            self.stack_layout.setCurrentWidget(self.label_not_time_varying)
            return

        self.stack_layout.setCurrentWidget(self.gw)

        self.clear_plot()
        if plot_type == PlotTypeWidget.PLOT_TIME:
            self.refresh_timeseries_plot()
        elif plot_type == PlotTypeWidget.PLOT_LONG_PROFILE:
            self.refresh_profile_plot()

    def clear_plot(self):
        for m in self.markers:
            iface.mapCanvas().scene().removeItem(m)
        self.markers = []
        self.plot.clear()
        self.clear_plot_legend()

    def clear_plot_legend(self):
        layout = self.plot.legend.layout
        # bulk removal of everything based on code in LegendItem.py
        for sample, label in self.plot.legend.items:
            layout.removeItem(sample)
            sample.close()
            layout.removeItem(label)
            label.close()
        self.plot.legend.items = []
        self.plot.legend.updateSize()

    def refresh_timeseries_plot(self):
        self.plot.getAxis('bottom').setLabel('Time [h]')
        # re-add curves
        for i, geometry in enumerate(self.point_picker.geometries):

            clr = colors[ i % len(colors) ]
            self.add_timeseries_plot(geometry, clr,self.point_picker.tool.searchRadiusMU(iface.mapCanvas()))

            # add marker if the geometry is not temporary
            if i != self.point_picker.temp_geometry_index:
                marker = QgsVertexMarker(iface.mapCanvas())
                marker.setColor(clr)
                marker.setPenWidth(2)
                marker.setCenter(geometry.asPoint())
                self.markers.append(marker)

    def add_timeseries_plot(self, geom_pt, clr,searchRadius):

        ds_group_index = self.current_dataset_group()

        x, y = timeseries_plot_data(self.layer, ds_group_index, geom_pt,searchRadius)
        self.plot.getAxis('left').setLabel(self.dataset_group_name(ds_group_index))
        self.plot.legend.setVisible(False)

        valid_plot = not all(map(math.isnan, y))
        if not valid_plot:
            return

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        return self.plot.plot(x=x, y=y, connect='finite', pen=pen)

    def refresh_profile_plot(self):
        self.plot.getAxis('bottom').setLabel('Distance [map unit]')
        profile = self.profile_picker.profile()

        if len(profile) < 2:
            return

        ds_group_index = self.current_dataset_group()
        self.plot.getAxis('left').setLabel(self.dataset_group_name(ds_group_index))
        dataset_indexes = self.btn_datasets.datasets
        isCurrentDataset = len(dataset_indexes) == 0
        if isCurrentDataset:
            dataset_indexes = self.currentDatasetsForDatasetGroup()

        self.plot.legend.setVisible(len(dataset_indexes) > 1)

        #add vertical lines on vertices position
        s=0
        pen=pyqtgraph.mkPen(color=(200,100,0), style=QtCore.Qt.DashDotLine)
        if self.chckBox_verticalLine.isChecked():
            for i in range(len(profile) - 1):
                p1 = profile[i]
                p2 = profile[i + 1]
                s = s+p1.distance(p2)
                vertLine = self.plot.addLine(s)
                vertLine.setPen(pen)


        for i in dataset_indexes:
            x, y = profile_1D_plot_data(self.layer,ds_group_index, i, profile)

            valid_plot = not all(map(math.isnan, y)) #is it necessary ? it will be good to tolerate nan
            if not valid_plot:
                continue

            colorIndex = i
            if isCurrentDataset:  # current dataset, used same color for all dataset for animation
                colorIndex = 0
            clr = colors[colorIndex % len(colors)]
            pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
            meta = self.layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(ds_group_index, i))
            p = self.plot.plot(x=x, y=y, connect='finite', pen=pen, name=time_to_string(self.layer, meta.time()))

    def dataset_group_is_not_time_varying(self, dataset_group_index):
        if dataset_group_index is None:
            return True

        if dataset_group_index < 0:
            return True

        if not self.layer or not self.layer.dataProvider():
            return True

        return self.layer.dataProvider().datasetCount(dataset_group_index) < 2

    def dataset_group_name(self, group_index):
        if group_index is None or group_index < 0 or self.layer is None or self.layer.dataProvider() is None:
            return "current"
        else:
            meta = self.layer.dataProvider().datasetGroupMetadata(group_index)
            return meta.name()

    def currentDatasetsForDatasetGroup(self):
        timeRange=iface.mapCanvas().temporalRange()
        dataset_index = self.layer.activeScalarDatasetAtTime(timeRange).dataset()
        if dataset_index < 0:
            return []
        else:
            return [dataset_index]