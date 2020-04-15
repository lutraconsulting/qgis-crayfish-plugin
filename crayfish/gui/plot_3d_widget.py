# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2016 Lutra Consulting

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

from ..plot import colors, plot_3d_data
from .utils import time_to_string
from .plot_cf_layer_widget import CrayfishLayerWidget
from .plot_point_geometry_widget import PointGeometryPickerWidget
from .plot_datasets_widget import DatasetsWidget
from .plot_dataset_groups_widget import DatasetGroupsWidget

class CrayfishPlot3dWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.layer = None

        self.btn_layer = CrayfishLayerWidget()
        self.btn_layer.layer_changed.connect(self.on_layer_changed)

        self.btn_dataset_group = DatasetGroupsWidget()
        self.btn_dataset_group.dataset_groups_changed.connect(self.on_dataset_group_changed)

        self.point_picker = PointGeometryPickerWidget()
        self.point_picker.geometries_changed.connect(self.on_geometries_changed)

        self.btn_pick_points = QPushButton("Pick points")
        self.btn_pick_points.clicked.connect(self.start_picking_points)

        self.btn_datasets = DatasetsWidget()
        self.btn_datasets.datasets_changed.connect(self.on_datasets_changed)

        self.markers = []  # for point

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()

        self.label_no_layer = QLabel("No mesh layer is selected.")
        self.label_no_layer.setAlignment(Qt.AlignCenter)

        self.stack_layout = QStackedLayout()
        self.stack_layout.addWidget(self.gw)
        self.stack_layout.addWidget(self.label_no_layer)

        hl = QHBoxLayout()
        hl.addWidget(self.btn_layer)
        hl.addWidget(self.btn_dataset_group)
        hl.addWidget(self.btn_datasets)
        hl.addWidget(self.point_picker)
        hl.addWidget(self.btn_pick_points)
        hl.addStretch()

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addLayout(self.stack_layout)
        self.setLayout(l)

        # init GUI
        self.on_dataset_group_changed(self.btn_dataset_group.dataset_groups)

        self.refresh_plot()

        iface.mapCanvas().temporalRangeChanged.connect(self.on_canvas_time_range_changed)

    def hideEvent(self, e):
        self.reset_widget()
        QWidget.hideEvent(self, e)

    def set_layer(self, layer):
        self.btn_layer.set_layer(layer)

    def clear_plot_legend(self):
        self.plot.legend.setVisible(False)
        layout = self.plot.legend.layout
        # bulk removal of everything based on code in LegendItem.py
        for sample, label in self.plot.legend.items:
            layout.removeItem(sample)
            sample.close()
            layout.removeItem(label)
            label.close()
        self.plot.legend.items = []
        self.plot.legend.updateSize()

    def on_layer_changed(self, layer):
        self.layer = layer
        self.btn_dataset_group.set_layer(layer)
        self.btn_datasets.set_layer(layer)
        self.reset_widget()

    def on_dataset_group_changed(self, lst):
        if len(lst) == 0:
            self.btn_datasets.set_dataset_group(self.layer.rendererSettings().activeScalarDatasetGroup() if self.layer is not None else None)
        elif len(lst) == 1:
            self.btn_datasets.set_dataset_group(lst[0])

        self.refresh_plot()

    def on_canvas_time_range_changed(self):
        if len(self.btn_datasets.datasets) == 0:
            self.refresh_plot()

    def current_dataset(self):
        dataset_indexes = self.btn_datasets.datasets
        if len(dataset_indexes) == 0:
            dataset_indexes = self.currentDatasetsForDatasetGroup()
        if len(dataset_indexes) != 0:
            return dataset_indexes[0]
        else:
            return -1;

    def current_dataset_group(self):
        dataset_groups = self.btn_dataset_group.dataset_groups
        if len(dataset_groups) == 0:
          return self.layer.rendererSettings().activeScalarDatasetGroup() if self.layer is not None else None
        else:
          return dataset_groups[0]

    def on_geometries_changed(self):
        self.refresh_plot()

    def on_datasets_changed(self, lst):
        self.refresh_plot()

    def start_picking_points(self):
        self.point_picker.start_picking_map()

    def reset_widget(self):
        self.point_picker.clear_geometries()
        self.point_picker.stop_picking()
        self.refresh_plot()

    def refresh_plot(self):
        if self.layer is None:
            self.stack_layout.setCurrentWidget(self.label_no_layer)
            return

        geoms = self.point_picker.geometries
        ds_group_index = self.current_dataset_group()
        ds_dataset_index = self.current_dataset()
        self.stack_layout.setCurrentWidget(self.gw)
        self.clear_plot()
        if geoms and ds_group_index is not None and ds_dataset_index is not None:
            self.refresh_3d_plot(self.layer, ds_group_index, ds_dataset_index, geoms)

    def clear_plot(self):
        for m in self.markers:
            iface.mapCanvas().scene().removeItem(m)
        self.markers = []
        self.plot.clear()
        self.clear_plot_legend()
        self.plot.setTitle("")

    def refresh_3d_plot(self, layer, ds_group_index, ds_dataset_index, geoms):
        self.plot.getAxis('bottom').setLabel('Magnitude')
        self.plot.getAxis('left').setLabel('Height')
        self.plot.legend.setVisible(False)

        # re-add curves
        for i, geometry in enumerate(geoms):

            clr = colors[ i % len(colors) ]
            self.add_3d_plot(layer, ds_group_index, ds_dataset_index, geometry, clr)

            # add marker if the geometry is not temporary
            if i != self.point_picker.temp_geometry_index:
                marker = QgsVertexMarker(iface.mapCanvas())
                marker.setColor(clr)
                marker.setPenWidth(2)
                marker.setCenter(geometry.asPoint())
                self.markers.append(marker)

        ds = QgsMeshDatasetIndex(ds_group_index, ds_dataset_index)
        meta = self.layer.dataProvider().datasetMetadata(ds)
        grpmeta = self.layer.dataProvider().datasetGroupMetadata(ds_group_index)
        name = grpmeta.name() + " @ " + time_to_string(self.layer, meta.time())
        self.plot.setTitle(name)
        self.plot.legend.setVisible(True)

    def add_3d_plot(self, layer, ds_group_index, ds_dataset_index, geom_pt, clr):
        x, y, average = plot_3d_data(layer, ds_group_index, ds_dataset_index, geom_pt)

        valid_plot = not all(map(math.isnan, y))
        if not valid_plot:
            return

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        name = None
        if average is not None:
            name = '{0:.4f}'.format(average)
        return self.plot.plot(x=x, y=y, name=name, connect='finite', pen=pen)

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
