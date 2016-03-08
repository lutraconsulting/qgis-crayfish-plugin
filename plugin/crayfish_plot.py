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
import math

from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
import pyqtgraph

from .crayfish_gui_utils import timeToString
from .crayfish_plot_cf_layer_widget import CrayfishLayerWidget
from .crayfish_plot_line_geometry_widget import LineGeometryPickerWidget
from .crayfish_plot_point_geometry_widget import PointGeometryPickerWidget
from .crayfish_plot_output_widget import OutputsWidget
from .crayfish_plot_dataset_widget import DatasetsWidget

pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')
pyqtgraph.setConfigOption('antialias', True)

# copied over from qgscolorscheme.cpp
# we can't really use the colors directly as they are - we do not want
# plain black and white colors and we first want to use more distinctive ones
colors = [
    # darker colors
    QColor( "#1f78b4" ),
    QColor( "#33a02c" ),
    QColor( "#e31a1c" ),
    QColor( "#ff7f00" ),
    # lighter colors
    QColor( "#a6cee3" ),
    QColor( "#b2df8a" ),
    QColor( "#fb9a99" ),
    QColor( "#fdbf6f" ),
]


def timeseries_plot_data(ds, geometry):
    """ return array with tuples defining X,Y points for plot """

    pt = geometry.asPoint()
    x,y = [], []

    for output in ds.outputs():
        t = output.time()

        value = ds.mesh().value(output, pt.x(), pt.y())
        if value == -9999.0:
            value = float("nan")
        x.append(t)
        y.append(value)

    return x, y

def cross_section_plot_data(output, geometry):
    """ return array with tuples defining X,Y points for plot """

    mesh = output.dataset().mesh()
    offset = 0
    step = 1
    length = geometry.length()
    x,y = [], []

    while offset < length:
        pt = geometry.interpolate(offset).asPoint()

        value = mesh.value(output, pt.x(), pt.y())
        if value != -9999.0:
            x.append(offset)
            y.append(value)

        offset += step

    return x, y




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


class CrayfishPlotWidget(QWidget):

    def __init__(self, layer, parent=None):
        QWidget.__init__(self, parent)

        self.layer = layer

        self.btn_layer = CrayfishLayerWidget(self.layer)
        self.btn_layer.layer_changed.connect(self.on_layer_changed)

        self.btn_dataset = DatasetsWidget(self.layer)
        self.btn_dataset.datasets_changed.connect(self.on_datasets_changed)

        self.btn_plot_type = PlotTypeWidget()
        self.btn_plot_type.plot_type_changed.connect(self.on_plot_type_changed)

        self.point_picker = PointGeometryPickerWidget()
        self.point_picker.geometries_changed.connect(self.on_geometries_changed)

        self.line_picker = LineGeometryPickerWidget()
        self.line_picker.geometries_changed.connect(self.on_geometries_changed)

        self.btn_output = OutputsWidget(self.layer)
        self.btn_output.outputs_changed.connect(self.on_outputs_changed)

        self.markers = []      # for points
        self.rubberbands = []  # for lines

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()

        hl = QHBoxLayout()
        hl.addWidget(self.btn_layer)
        hl.addWidget(self.btn_plot_type)
        hl.addWidget(self.btn_dataset)
        hl.addWidget(self.btn_output)
        hl.addWidget(self.point_picker)
        hl.addWidget(self.line_picker)
        hl.addStretch()

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addWidget(self.gw)
        self.setLayout(l)

        # init GUI
        self.on_plot_type_changed(self.btn_plot_type.plot_type)
        self.on_datasets_changed(self.btn_dataset.datasets)

        # make picking from map (for time series) default
        self.point_picker.picker_clicked()


    def hideEvent(self, e):
        self.reset_widget()
        QWidget.hideEvent(self, e)


    def set_layer(self, layer):
        self.btn_layer.set_layer(layer)

    def on_layer_changed(self, layer):
        self.layer = layer
        self.btn_dataset.set_layer(layer)
        self.btn_output.set_layer(layer)
        self.reset_widget()

    def on_plot_type_changed(self, plot_type):
        self.point_picker.setVisible(plot_type == PlotTypeWidget.PLOT_TIME)
        self.line_picker.setVisible(plot_type == PlotTypeWidget.PLOT_CROSS_SECTION)
        self.btn_output.setVisible(plot_type == PlotTypeWidget.PLOT_CROSS_SECTION)

        if plot_type != PlotTypeWidget.PLOT_TIME:
            self.point_picker.clear_geometries()
            self.point_picker.stop_picking()
        if plot_type != PlotTypeWidget.PLOT_CROSS_SECTION:
            self.line_picker.clear_geometries()
            self.line_picker.stop_picking()

        self.refresh_plot()


    def on_datasets_changed(self, lst):
        if len(lst) == 0:
            self.btn_output.set_dataset(self.layer.currentDataSet())
        elif len(lst) == 1:
            self.btn_output.set_dataset(lst[0])

        self.refresh_plot()


    def on_geometries_changed(self):
        self.refresh_plot()


    def on_outputs_changed(self, lst):
        self.refresh_plot()

    def reset_widget(self):
        self.point_picker.clear_geometries()
        self.point_picker.stop_picking()
        self.line_picker.clear_geometries()
        self.line_picker.stop_picking()
        self.refresh_plot()

    def refresh_plot(self):
        plot_type = self.btn_plot_type.plot_type
        if plot_type == PlotTypeWidget.PLOT_TIME:
            self.refresh_timeseries_plot()
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
        self.clear_plot()
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

        datasets = self.btn_dataset.datasets
        if len(datasets) == 0:
          ds = self.layer.currentDataSet()
        else:
          ds = datasets[0]

        x, y = timeseries_plot_data(ds, geom_pt)
        self.plot.getAxis('left').setLabel(ds.name())
        self.plot.legend.setVisible(False)

        valid_plot = not all(map(math.isnan, y))
        if not valid_plot:
            return

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        return self.plot.plot(x=x, y=y, connect='finite', pen=pen)


    def refresh_cross_section_plot(self):
        self.clear_plot()
        self.plot.getAxis('bottom').setLabel('Station [m]')

        if len(self.line_picker.geometries) == 0:
            return

        geometry = self.line_picker.geometries[0]  # only using the first linestring

        if len(geometry.asPolyline()) == 0:
            return  # not a linestring?

        datasets = self.btn_dataset.datasets
        if len(datasets) == 0:
          ds = self.layer.currentDataSet()
        else:
          ds = datasets[0]

        self.plot.getAxis('left').setLabel(ds.name())

        outputs = self.btn_output.outputs
        if len(outputs) == 0:
            outputs = [self.layer.currentOutputForDataset(ds)]

        self.plot.legend.setVisible(len(outputs) > 1)

        for i, output in enumerate(outputs):

            x,y = cross_section_plot_data(output, geometry)

            valid_plot = not all(map(math.isnan, y))
            if not valid_plot:
                continue

            clr = colors[i % len(colors)]
            pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
            p = self.plot.plot(x=x, y=y, connect='finite', pen=pen, name=timeToString(output.time()))

        rb = QgsRubberBand(iface.mapCanvas(), QGis.Line)
        rb.setColor(colors[0])
        rb.setWidth(2)
        rb.setToGeometry(geometry, None)
        self.rubberbands.append(rb)
