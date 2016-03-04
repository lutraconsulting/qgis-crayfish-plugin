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


def timeseries_plot_data(layer, geometry):       # TODO: datasets
    """ return array with tuples defining X,Y points for plot """

    pt = geometry.asPoint()
    ds = layer.currentDataSet()
    x,y = [], []

    for output in ds.outputs():
        t = output.time()

        value = layer.mesh.value(output, pt.x(), pt.y())
        if value == -9999.0:
            value = float("nan")
        x.append(t)
        y.append(value)

    return x, y

def cross_section_plot_data(layer, geometry):    # TODO: outputs
    """ return array with tuples defining X,Y points for plot """

    offset = 0
    step = 1
    length = geometry.length()
    x,y = [], []

    while offset < length:
        pt = geometry.interpolate(offest).asPoint()

        value = layer.mesh.value(layer.currentOutput(), pt.x(), pt.y())
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

    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

        QgsMapLayerRegistry.instance().layersAdded.connect(self.layers_added)
        QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.layers_will_be_removed)

        self.layers_added( QgsMapLayerRegistry.instance().mapLayers().values() )

    def layers_added(self, lst):
        for layer in lst:
            if not isinstance(layer, QgsVectorLayer):
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


class CrayfishPlotWidget(QWidget):

    PICK_NO, PICK_MAP, PICK_LAYER = range(3)

    def __init__(self, layer, parent=None):
        QWidget.__init__(self, parent)

        self.layer = layer
        self.temp_plot_item = None
        self.pick_mode = self.PICK_NO
        self.pick_layer = None

        self.btn_picker = QToolButton()
        self.btn_picker.setText("From map")
        self.btn_picker.setCheckable(True)
        self.btn_picker.clicked.connect(self.picker_clicked)

        self.menu_layers = MapLayerMenu()

        self.btn_layer = QToolButton()
        self.btn_layer.setText("From layer")
        self.btn_layer.setPopupMode(QToolButton.InstantPopup)
        self.btn_layer.setMenu(self.menu_layers)
        self.menu_layers.picked_layer.connect(self.on_picked_layer)

        self.tool = PickGeometryTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)
        self.tool.setButton(self.btn_picker)

        self.markers = []

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)

        hl = QHBoxLayout()
        hl.addWidget(self.btn_picker)
        hl.addWidget(self.btn_layer)

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addWidget(self.gw)
        self.setLayout(l)

        self.picker_clicked()  # make picking from map default


    def picker_clicked(self):

        was_active = (self.pick_mode == self.PICK_MAP)
        self.stop_picking()

        if not was_active:
            self.start_picking_map()

    def start_picking_map(self):
        self.pick_mode = self.PICK_MAP
        iface.mapCanvas().setMapTool(self.tool)
        self.clear_plot()

    def stop_picking(self):
        if self.pick_mode == self.PICK_MAP:
            iface.mapCanvas().unsetMapTool(self.tool)
        elif self.pick_mode == self.PICK_LAYER:
            self.pick_layer.selectionChanged.disconnect(self.on_pick_selection_changed)
            self.pick_layer = None
        self.pick_mode = self.PICK_NO

    def clear_plot(self):
        for m in self.markers:
            self.tool.canvas().scene().removeItem(m)
        self.markers = []
        self.plot.clear()

    def add_plot(self, pt, permanent):

        x, y = timeseries_plot_data(self.layer, QgsGeometry.fromPoint(pt))
        self.plot.getAxis('bottom').setLabel('Time [h]')
        self.plot.getAxis('left').setLabel(self.layer.currentDataSet().name())
        clr = colors[ len(self.markers) % len(colors) ]

        valid_plot = not all(map(math.isnan, y))
        if not valid_plot:
            return

        if permanent:
            marker = QgsVertexMarker(iface.mapCanvas())
            marker.setColor(clr)
            marker.setPenWidth(2)
            marker.setCenter(pt)
            self.markers.append(marker)

        pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
        return self.plot.plot(x=x, y=y, connect='finite', pen=pen)

    def on_picked(self, pt, clicked, with_ctrl):

        if not with_ctrl and self.temp_plot_item:
            self.plot.removeItem(self.temp_plot_item)
            self.temp_plot_item = None

        p = self.add_plot(pt, clicked)
        if p and not clicked:
            self.temp_plot_item = p

        if clicked and not with_ctrl:  # no more updates
            self.stop_picking()


    def hideEvent(self, e):
        self.clear_plot()
        self.stop_picking()
        QWidget.hideEvent(self, e)


    def on_picked_layer(self, layer_id):

        self.stop_picking()

        self.pick_layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        if not self.pick_layer:
            return

        self.pick_mode = self.PICK_LAYER
        self.pick_layer.selectionChanged.connect(self.on_pick_selection_changed)

        self.on_pick_selection_changed()

    def on_pick_selection_changed(self):

        self.clear_plot()
        for f in self.pick_layer.selectedFeatures():
            self.add_plot(f.geometry().asPoint(), True)
