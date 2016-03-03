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
        #if value != -9999.0:
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



class CrayfishPlotWidget(QWidget):

    def __init__(self, layer, parent=None):
        QWidget.__init__(self, parent)

        self.layer = layer
        self.temp_plot_item = None

        self.btn_picker = QToolButton()
        self.btn_picker.setText("Pick point")
        self.btn_picker.setCheckable(True)
        self.btn_picker.clicked.connect(self.picker_clicked)

        self.tool = PickGeometryTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)
        self.tool.setButton(self.btn_picker)

        self.markers = []

        iface.mapCanvas().setMapTool(self.tool)

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)

        hl = QHBoxLayout()
        hl.addWidget(self.btn_picker)

        l = QVBoxLayout()
        l.addLayout(hl)
        l.addWidget(self.gw)
        self.setLayout(l)


    def picker_clicked(self):
        if iface.mapCanvas().mapTool() != self.tool:
            iface.mapCanvas().setMapTool(self.tool)
            self.clear_plot()
        else:
            iface.mapCanvas().unsetMapTool(self.tool)


    def clear_plot(self):
        for m in self.markers:
            self.tool.canvas().scene().removeItem(m)
        self.markers = []
        self.plot.clear()

    def on_picked(self, pt, clicked, with_ctrl):

        x, y = timeseries_plot_data(self.layer, QgsGeometry.fromPoint(pt))

        if not with_ctrl and self.temp_plot_item:
            self.plot.removeItem(self.temp_plot_item)
            self.temp_plot_item = None

        self.plot.getAxis('bottom').setLabel('Time [h]')
        self.plot.getAxis('left').setLabel(self.layer.currentDataSet().name())
        clr = colors[ len(self.markers) % len(colors) ]

        if not all(map(math.isnan, y)):
            pen = pyqtgraph.mkPen(color=clr, width=2, cosmetic=True)
            p = self.plot.plot(x=x, y=y, connect='finite', pen=pen)
            if not clicked:
                self.temp_plot_item = p

        if clicked:
            marker = QgsVertexMarker(iface.mapCanvas())
            marker.setColor(clr)
            marker.setPenWidth(2)
            marker.setCenter(pt)
            self.markers.append(marker)

        if clicked and not with_ctrl:  # no more updates
            iface.mapCanvas().unsetMapTool(self.tool)

    def hideEvent(self, e):
        self.clear_plot()
        QWidget.hideEvent(self, e)
