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

from crayfish_gui_utils import timeToString

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


class PickGeometryTool(QgsMapTool):

    picked = pyqtSignal(QgsPoint, bool, bool)   # point, whether clicked or just moving, whether clicked with Ctrl

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)

    def canvasMoveEvent(self, e):
        #if e.button() == Qt.LeftButton:
        self.picked.emit(e.mapPoint(), False, False)

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.picked.emit(e.mapPoint(), True, e.modifiers() & Qt.ControlModifier)

    def canvasReleaseEvent(self, e):
        pass


def geom2icon(geom_type):
    if geom_type == QGis.Point:
        return QgsLayerItem.iconPoint()
    elif geom_type == QGis.Polygon:
        return QgsLayerItem.iconPolygon()
    elif geom_type == QGis.Line:
        return QgsLayerItem.iconLine()
    else:
        return QIcon()


class MapLayerMenu(QMenu):

    picked_layer = pyqtSignal(unicode)

    def __init__(self, geom_type, parent=None):
        QMenu.__init__(self, parent)

        QgsMapLayerRegistry.instance().layersAdded.connect(self.layers_added)
        QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.layers_will_be_removed)

        self.geom_type = geom_type
        self.layers_added( QgsMapLayerRegistry.instance().mapLayers().values() )

    def layers_added(self, lst):
        for layer in lst:
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() != self.geom_type:
                continue
            a = self.addAction(geom2icon(layer.geometryType()), layer.name())
            a.layer_id = layer.id()
            a.triggered.connect(self.triggered_action)

    def layers_will_be_removed(self, lst):
        for action in self.actions():
            if action.layer_id in lst:
                self.removeAction(action)

    def triggered_action(self):
        self.picked_layer.emit(self.sender().layer_id)


class DatasetsMenu(QMenu):

    datasets_changed = pyqtSignal(list)

    def __init__(self, layer, parent=None):
        QMenu.__init__(self, parent)

        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.triggered_action_current)
        self.addSeparator()

        layer.currentDataSetChanged.connect(self.on_current_dataset_changed)

        for ds in layer.mesh.datasets():
            a = self.addAction(ds.name())
            a.ds = ds
            a.setCheckable(True)
            a.triggered.connect(self.triggered_action)

    def triggered_action(self):
        for a in self.actions():
          a.setChecked(a == self.sender())
        self.datasets_changed.emit([self.sender().ds])

    def triggered_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.datasets_changed.emit([])

    def on_current_dataset_changed(self):
        if self.action_current.isChecked():
            self.datasets_changed.emit([])  # re-emit changed signal


class PointGeometryPickerWidget(QWidget):

    geometries_changed = pyqtSignal()

    PICK_NO, PICK_MAP, PICK_LAYER = range(3)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.pick_mode = self.PICK_NO
        self.pick_layer = None
        self.geometries = []
        self.temp_geometry_index = -1

        self.btn_picker = QToolButton()
        self.btn_picker.setText("From map")
        self.btn_picker.setCheckable(True)
        self.btn_picker.clicked.connect(self.picker_clicked)

        self.menu_layers = MapLayerMenu(QGis.Point)

        self.btn_layer = QToolButton()
        self.btn_layer.setText("From layer")
        self.btn_layer.setPopupMode(QToolButton.InstantPopup)
        self.btn_layer.setMenu(self.menu_layers)
        self.menu_layers.picked_layer.connect(self.on_picked_layer)

        self.tool = PickGeometryTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)
        self.tool.setButton(self.btn_picker)

        layout = QHBoxLayout()
        layout.addWidget(self.btn_picker)
        layout.addWidget(self.btn_layer)

        self.setLayout(layout)

        self.picker_clicked()  # make picking from map default

    def clear_geometries(self):
        self.geometries = []
        self.temp_geometry_index = -1
        self.geometries_changed.emit()

    def picker_clicked(self):

        was_active = (self.pick_mode == self.PICK_MAP)
        self.stop_picking()

        if not was_active:
            self.start_picking_map()

    def start_picking_map(self):
        self.pick_mode = self.PICK_MAP
        iface.mapCanvas().setMapTool(self.tool)
        self.clear_geometries()

    def stop_picking(self):
        if self.pick_mode == self.PICK_MAP:
            iface.mapCanvas().unsetMapTool(self.tool)
        elif self.pick_mode == self.PICK_LAYER:
            self.pick_layer.selectionChanged.disconnect(self.on_pick_selection_changed)
            self.pick_layer = None
        self.pick_mode = self.PICK_NO

    def on_picked(self, pt, clicked, with_ctrl):

        geom = QgsGeometry.fromPoint(pt)
        if clicked:
            if self.temp_geometry_index == -1:
                self.geometries.append(geom)
            else:
                self.geometries[self.temp_geometry_index] = geom
                self.temp_geometry_index = -1
        else:   # just doing mouse move
            if self.temp_geometry_index == -1:
                self.temp_geometry_index = len(self.geometries)
                self.geometries.append(geom)
            else:
                self.geometries[self.temp_geometry_index] = geom

        self.geometries_changed.emit()

        if clicked and not with_ctrl:  # no more updates
            self.stop_picking()

    def on_picked_layer(self, layer_id):

        self.stop_picking()

        self.pick_layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        if not self.pick_layer:
            return

        self.pick_mode = self.PICK_LAYER
        self.pick_layer.selectionChanged.connect(self.on_pick_selection_changed)

        self.on_pick_selection_changed()

    def on_pick_selection_changed(self):

        self.geometries = [QgsGeometry(f.geometry()) for f in self.pick_layer.selectedFeatures()]
        self.temp_geometry_index = -1
        self.geometries_changed.emit()


class LineGeometryPickerWidget(QWidget):

    geometries_changed = pyqtSignal()

    PICK_NO, PICK_MAP, PICK_LAYER = range(3)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.pick_mode = self.PICK_NO
        self.pick_layer = None
        self.geometries = []
        #self.temp_geometry_index = -1

        self.menu_layers = MapLayerMenu(QGis.Line)

        self.btn_layer = QToolButton()
        self.btn_layer.setText("From layer")
        self.btn_layer.setPopupMode(QToolButton.InstantPopup)
        self.btn_layer.setMenu(self.menu_layers)
        self.menu_layers.picked_layer.connect(self.on_picked_layer)

        layout = QHBoxLayout()
        #layout.addWidget(self.btn_picker)
        layout.addWidget(self.btn_layer)
        self.setLayout(layout)

    def stop_picking(self):
        if self.pick_mode == self.PICK_MAP:
            pass    # TODO: iface.mapCanvas().unsetMapTool(self.tool)
        elif self.pick_mode == self.PICK_LAYER:
            self.pick_layer.selectionChanged.disconnect(self.on_pick_selection_changed)
            self.pick_layer = None
        self.pick_mode = self.PICK_NO

    def on_picked_layer(self, layer_id):

        self.stop_picking()

        self.pick_layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        if not self.pick_layer:
            return

        self.pick_mode = self.PICK_LAYER
        self.pick_layer.selectionChanged.connect(self.on_pick_selection_changed)

        self.on_pick_selection_changed()

    def on_pick_selection_changed(self):

        self.geometries = [QgsGeometry(f.geometry()) for f in self.pick_layer.selectedFeatures()]
        #self.temp_geometry_index = -1
        self.geometries_changed.emit()


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


class OutputsMenu(QMenu):

    outputs_changed = pyqtSignal(list)

    def __init__(self, layer, parent=None):
        QMenu.__init__(self, parent)

        self.set_dataset(None)

        layer.currentOutputTimeChanged.connect(self.on_current_output_time_changed)

    def set_dataset(self, ds):

        # populate timesteps
        self.clear()
        self.action_current = self.addAction("[current]")
        self.action_current.setCheckable(True)
        self.action_current.setChecked(True)
        self.action_current.triggered.connect(self.on_action_current)
        self.addSeparator()

        if ds is None:
            return

        for output in ds.outputs():
            a = self.addAction(timeToString(output.time()))
            a.output = output
            a.setCheckable(True)
            a.triggered.connect(self.on_action)

    def on_action(self):
        for a in self.actions():
            a.setChecked(a == self.sender())
        self.outputs_changed.emit([self.sender().output])

    def on_action_current(self):
        for a in self.actions():
            a.setChecked(a == self.action_current)
        self.outputs_changed.emit([])

    def on_current_output_time_changed(self):
        if self.action_current.isChecked():
            self.outputs_changed.emit([])   # re-emit


class CrayfishPlotWidget(QWidget):

    PLOT_TIME, PLOT_CROSS_SECTION = range(2)

    def __init__(self, layer, parent=None):
        QWidget.__init__(self, parent)

        self.layer = layer

        self.menu_datasets = DatasetsMenu(self.layer)

        self.btn_dataset = QToolButton()
        self.btn_dataset.setPopupMode(QToolButton.InstantPopup)
        self.btn_dataset.setMenu(self.menu_datasets)
        self.menu_datasets.datasets_changed.connect(self.on_datasets_changed)

        self.menu_plot_types = PlotTypeMenu()

        self.btn_plot_type = QToolButton()
        self.btn_plot_type.setPopupMode(QToolButton.InstantPopup)
        self.btn_plot_type.setMenu(self.menu_plot_types)
        self.menu_plot_types.plot_type_changed.connect(self.on_plot_type_changed)

        self.point_picker = PointGeometryPickerWidget()
        self.point_picker.geometries_changed.connect(self.on_geometries_changed)

        self.line_picker = LineGeometryPickerWidget()
        self.line_picker.geometries_changed.connect(self.on_geometries_changed)

        self.menu_outputs = OutputsMenu(self.layer)

        self.btn_output = QToolButton()
        self.btn_output.setPopupMode(QToolButton.InstantPopup)
        self.btn_output.setMenu(self.menu_outputs)
        self.menu_outputs.outputs_changed.connect(self.on_outputs_changed)

        self.plot_type = self.PLOT_TIME
        self.datasets = []
        self.outputs = []   # only for cross-section plot
        self.markers = []      # for points
        self.rubberbands = []  # for lines

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)

        hl = QHBoxLayout()
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

        self.on_plot_type_changed(self.PLOT_TIME)
        self.on_datasets_changed([])  # make the current dataset default
        self.on_outputs_changed([])


    def hideEvent(self, e):
        self.point_picker.clear_geometries()
        self.point_picker.stop_picking()
        # TODO: handle also line_picker
        QWidget.hideEvent(self, e)


    def on_plot_type_changed(self, plot_type):
        self.plot_type = plot_type
        self.btn_plot_type.setText("Plot: " + self.menu_plot_types.names[self.plot_type])
        self.point_picker.setVisible(self.plot_type == self.PLOT_TIME)
        self.line_picker.setVisible(self.plot_type == self.PLOT_CROSS_SECTION)
        self.btn_output.setVisible(self.plot_type == self.PLOT_CROSS_SECTION)

        if self.plot_type != self.PLOT_TIME:
            self.point_picker.clear_geometries()
            self.point_picker.stop_picking()

        # TODO: handle also line_picker cleanup

        self.refresh_plot()


    def on_datasets_changed(self, lst):
        self.datasets = lst
        if len(lst) == 0:
            self.btn_dataset.setText("Dataset: [current]")
            self.menu_outputs.set_dataset(self.layer.currentDataSet())
        elif len(lst) == 1:
            self.btn_dataset.setText("Dataset: " + lst[0].name())
            self.menu_outputs.set_dataset(lst[0])

        self.refresh_plot()


    def on_geometries_changed(self):
        self.refresh_plot()


    def on_outputs_changed(self, lst):
        self.outputs = lst
        if len(lst) == 0:
            self.btn_output.setText("Time: [current]")
        elif len(lst) == 1:
            self.btn_output.setText("Time: " + timeToString(lst[0].time()))

        self.refresh_plot()


    def refresh_plot(self):
        if self.plot_type == self.PLOT_TIME:
            self.refresh_timeseries_plot()
        elif self.plot_type == self.PLOT_CROSS_SECTION:
            self.refresh_cross_section_plot()

    def clear_plot(self):
        for m in self.markers:
            iface.mapCanvas().scene().removeItem(m)
        self.markers = []
        for rb in self.rubberbands:
            iface.mapCanvas().scene().removeItem(rb)
        self.rubberbands = []
        self.plot.clear()


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

        if len(self.datasets) == 0:
          ds = self.layer.currentDataSet()
        else:
          ds = self.datasets[0]

        x, y = timeseries_plot_data(ds, geom_pt)
        self.plot.getAxis('left').setLabel(ds.name())

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
        clr = colors[0]

        if len(geometry.asPolyline()) == 0:
            return  # not a linestring?

        if len(self.datasets) == 0:
          ds = self.layer.currentDataSet()
        else:
          ds = self.datasets[0]

        if len(self.outputs) == 0:
            output = self.layer.currentOutputForDataset(ds)
        else:
            output = self.outputs[0]  # TODO: multiple outputs

        x,y = cross_section_plot_data(output, geometry)
        self.plot.getAxis('left').setLabel(output.dataset().name())

        print "output", output
        print "x", x
        print "y", y

        valid_plot = not all(map(math.isnan, y))
        if not valid_plot:
            return

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        p = self.plot.plot(x=x, y=y, connect='finite', pen=pen)

        rb = QgsRubberBand(iface.mapCanvas(), QGis.Line)
        rb.setColor(clr)
        rb.setWidth(2)
        rb.setToGeometry(geometry, None)
        self.rubberbands.append(rb)
