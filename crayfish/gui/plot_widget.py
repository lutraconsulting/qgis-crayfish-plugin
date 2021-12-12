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
    import crayfish.pyqtgraph_0_12_2 as pyqtgraph

from ..plot import timeseries_plot_data, cross_section_plot_data, colors, integral_plot_data
from .utils import time_to_string
from .plot_cf_layer_widget import CrayfishLayer2dWidget
from .plot_line_geometry_widget import LineGeometryPickerWidget
from .plot_point_geometry_widget import PointGeometryPickerWidget
from .plot_datasets_widget import DatasetsWidget
from .plot_dataset_groups_widget import DatasetGroupsWidget
from .plot_map_layer_widget import MapLayersWidget

class PlotTypeMenu(QMenu):

    plot_type_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.names = ["Time series", "Cross-section"]
        for i, plot_type_name in enumerate(self.names):
            a = self.addAction(plot_type_name)
            a.plot_type = i
            a.triggered.connect(self.on_action)

    def on_action(self):
        self.plot_type_changed.emit(self.sender().plot_type)


class PlotTypeWidget(QToolButton):

    plot_type_changed = pyqtSignal(int)

    PLOT_TIME, PLOT_CROSS_SECTION = range(2)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(QgsApplication.getThemeIcon("/histogram.png"))

        self.menu_plot_types = PlotTypeMenu()

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


class GeomTypeMenu(QMenu):

    geom_type_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        self.names = ['Point', 'Line']
        for i, geom_type_name in enumerate(self.names):
            a = self.addAction(geom_type_name)
            a.geom_type = i
            a.triggered.connect(self.on_action)

    def on_action(self):
        self.geom_type_changed.emit(self.sender().geom_type)


class GeometryTypeWidget(QToolButton):

    geometry_type_changed = pyqtSignal(int)

    POINT, LINE = range(2)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(QgsApplication.getThemeIcon("/histogram.png"))

        self.menu_geometry_types = GeomTypeMenu()

        self.setPopupMode(QToolButton.InstantPopup)
        self.setMenu(self.menu_geometry_types)
        self.menu_geometry_types.geom_type_changed.connect(self.on_geometry_type_changed)

        self.set_geometry_type(self.POINT)

    def set_geometry_type(self, geometry_type):
        self.on_geometry_type_changed(geometry_type)

    def on_geometry_type_changed(self, geometry_type):
        self.geometry_type = geometry_type
        self.setText("From Map: " + self.menu_geometry_types.names[self.geometry_type])
        self.geometry_type_changed.emit(geometry_type)


class CrayfishPlotWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.layer = None

        self.btn_layer = CrayfishLayer2dWidget()
        self.btn_layer.layer_changed.connect(self.on_layer_changed)

        self.btn_dataset_group = DatasetGroupsWidget()
        self.btn_dataset_group.dataset_groups_changed.connect(self.on_dataset_group_changed)

        self.btn_plot_type = PlotTypeWidget()
        self.btn_plot_type.plot_type_changed.connect(self.on_plot_type_changed)

        self.btn_geom_type = GeometryTypeWidget()
        self.btn_geom_type.geometry_type_changed.connect(self.on_geometry_type_changed)

        self.point_picker = PointGeometryPickerWidget()
        self.point_picker.geometries_changed.connect(self.on_geometries_changed)

        self.btn_from_pt_layer = MapLayersWidget(QgsWkbTypes.Point)
        self.btn_from_pt_layer.picked_layer.connect(self.point_picker.on_picked_layer)

        self.line_picker = LineGeometryPickerWidget()
        self.line_picker.geometries_changed.connect(self.on_geometries_changed)

        self.btn_from_line_layer = MapLayersWidget(QgsWkbTypes.LineString)
        self.btn_from_line_layer.picked_layer.connect(self.line_picker.on_picked_layer)

        self.btn_datasets = DatasetsWidget()
        self.btn_datasets.datasets_changed.connect(self.on_datasets_changed)

        self.btn_options = QToolButton()
        self.btn_options.setAutoRaise(True)
        self.btn_options.setToolTip("Plot Options")
        self.btn_options.setIcon(QgsApplication.getThemeIcon( "/mActionOptions.svg" ))
        self.btn_options.clicked.connect(self.on_options_clicked)

        self.markers = []      # for points
        self.rubberbands = []  # for lines

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
        hl.addWidget(self.btn_geom_type)
        hl.addWidget(self.point_picker)
        hl.addWidget(self.btn_from_pt_layer)
        hl.addWidget(self.line_picker)
        hl.addWidget(self.btn_from_line_layer)
        hl.addStretch()
        hl.addWidget(self.btn_options)

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addLayout(self.stack_layout)
        self.setLayout(l)

        # init GUI
        self.on_plot_type_changed(self.btn_plot_type.plot_type)
        self.on_geometry_type_changed(self.btn_geom_type.geometry_type)
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
        self.reset_widget()

    def on_plot_type_changed(self, plot_type):
        self.line_picker.setVisible(plot_type == PlotTypeWidget.PLOT_CROSS_SECTION)
        self.btn_datasets.setVisible(plot_type == PlotTypeWidget.PLOT_CROSS_SECTION)
        self.btn_geom_type.setVisible(plot_type == PlotTypeWidget.PLOT_TIME)
        self.btn_from_pt_layer.setVisible(plot_type == PlotTypeWidget.PLOT_TIME)
        self.btn_from_line_layer.setVisible(plot_type == PlotTypeWidget.PLOT_CROSS_SECTION)

        if plot_type != PlotTypeWidget.PLOT_TIME:
            self.point_picker.clear_geometries()
            self.point_picker.stop_picking()

        self.line_picker.stop_picking()

        self.refresh_plot()

    def on_geometry_type_changed(self, geom_type):
        self.btn_from_pt_layer.setVisible(geom_type == GeometryTypeWidget.POINT)
        self.btn_from_line_layer.setVisible(geom_type == GeometryTypeWidget.LINE)

        if geom_type != GeometryTypeWidget.POINT:
            self.point_picker.clear_geometries()
            self.point_picker.stop_picking()
            self.line_picker.start_picking_map()
        elif geom_type != GeometryTypeWidget.LINE:
            self.line_picker.clear_geometries()
            self.line_picker.stop_picking()
            self.point_picker.start_picking_map()

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

    def on_geometries_changed(self):
        self.refresh_plot()


    def on_datasets_changed(self, lst):
        self.refresh_plot()

    def on_canvas_time_range_changed(self):
        if len(self.btn_datasets.datasets) == 0:
            self.refresh_plot()

    def reset_widget(self):
        self.point_picker.clear_geometries()
        self.point_picker.stop_picking()
        self.line_picker.clear_geometries()
        self.line_picker.stop_picking()
        self.refresh_plot()

    def refresh_plot(self):
        plot_type = self.btn_plot_type.plot_type
        geom_type = self.btn_geom_type.geometry_type

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
            if geom_type == GeometryTypeWidget.POINT:
                self.refresh_timeseries_plot()
            elif geom_type == GeometryTypeWidget.LINE:
                self.refresh_integral_plot()
            else:
                pass
        elif plot_type == PlotTypeWidget.PLOT_CROSS_SECTION:
            self.refresh_cross_section_plot()

    def clear_plot(self):
        for m in self.markers:
            iface.mapCanvas().scene().removeItem(m)
        self.markers = []
        for rb in self.rubberbands:
            iface.mapCanvas().scene().removeItem(rb)
        self.rubberbands = []
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
            self.add_timeseries_plot(geometry, clr)

            # add marker if the geometry is not temporary
            if i != self.point_picker.temp_geometry_index:
                marker = QgsVertexMarker(iface.mapCanvas())
                marker.setColor(clr)
                marker.setPenWidth(2)
                marker.setCenter(geometry.asPoint())
                self.markers.append(marker)

    def add_timeseries_plot(self, geom_pt, clr):

        ds_group_index = self.current_dataset_group()

        x, y = timeseries_plot_data(self.layer, ds_group_index, geom_pt)
        self.plot.getAxis('left').setLabel(self.dataset_group_name(ds_group_index))
        self.plot.legend.setVisible(False)

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        return self.plot.plot(x=x, y=y, connect='finite', pen=pen)

    def refresh_cross_section_plot(self):
        self.plot.getAxis('bottom').setLabel('Station [m]')

        if len(self.line_picker.geometries) == 0:
            return

        geometry = self.line_picker.geometries[0]  # only using the first linestring

        if len(geometry.asPolyline()) == 0:
            return  # not a linestring?

        ds_group_index = self.current_dataset_group()

        self.plot.getAxis('left').setLabel(self.dataset_group_name(ds_group_index))

        dataset_indexes = self.btn_datasets.datasets
        isCurrentDataset = len(dataset_indexes) == 0
        if isCurrentDataset:
            dataset_indexes = self.currentDatasetsForDatasetGroup()

        self.plot.legend.setVisible(len(dataset_indexes) > 1)

        s = QSettings()
        plot_resolution = s.value('/crayfish/cross_section_resolution', 1., type=float)

        for i in dataset_indexes:
            x,y = cross_section_plot_data(self.layer, ds_group_index, i, geometry, plot_resolution)

            valid_plot = not all(map(math.isnan, y))
            if not valid_plot:
                continue

            colorIndex = i
            if isCurrentDataset : #current dataset, used same color for all dataset for animation
                colorIndex = 0
            clr = colors[colorIndex % len(colors)]
            pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
            meta = self.layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(ds_group_index, i))
            p = self.plot.plot(x=x, y=y, connect='finite', pen=pen, name=time_to_string(self.layer, meta.time()))

        rb = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        rb.setColor(colors[0])
        rb.setWidth(2)
        rb.setToGeometry(geometry, None)
        self.rubberbands.append(rb)

    def refresh_integral_plot(self):
        self.plot.getAxis('bottom').setLabel('Time [h]')

        if len(self.line_picker.geometries) == 0:
            return

        # this can be extended for more features
        geometry = self.line_picker.geometries[0]  # only using the first linestring

        if len(geometry.asPolyline()) == 0:
            return  # not a linestring?

        ds_group_index = self.current_dataset_group()

        split = self.dataset_group_name(ds_group_index).split('[')
        variable = split[0]
        try:
            unit = split[1].split(']')[0]
            self.plot.getAxis('left').setLabel('Integral of {} [{}.m]'.format(variable, unit))
        except IndexError:
            self.plot.getAxis('left').setLabel('Integral of {} [m]'.format(variable))

        s = QSettings()
        plot_resolution = s.value('/crayfish/cross_section_resolution', 1., type=float)

        x, y = integral_plot_data(self.layer, ds_group_index, geometry, plot_resolution)

        clr = colors[0 % len(colors)]
        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        p = self.plot.plot(x=x, y=y, connect='finite', pen=pen)

        rb = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        rb.setColor(colors[0])
        rb.setWidth(2)
        rb.setToGeometry(geometry, None)
        self.rubberbands.append(rb)

    def on_options_clicked(self):
        s = QSettings()
        value = s.value('/crayfish/cross_section_resolution', 1., type=float)

        value, res = QInputDialog.getDouble(None, 'Plot Options', 'Cross-section plot resolution [map units]',
                                            value, 0.000001, 1000000, 6)
        if not res:
            return

        s.setValue('/crayfish/cross_section_resolution', value)

        self.refresh_plot()

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
        dataset_group = self.current_dataset_group()
        if self.layer.temporalProperties().isActive and iface.mapCanvas().mapSettings().isTemporal():
            timeRange = iface.mapCanvas().temporalRange()
            dataset_index = self.layer.datasetIndexAtTime(timeRange, dataset_group).dataset()
        else:
            dataset_index = self.layer.staticScalarDatasetIndex().dataset()

        if dataset_index < 0:
            return []
        else:
            return [dataset_index]
