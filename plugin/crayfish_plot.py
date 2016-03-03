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

    picked = pyqtSignal(QgsPoint, bool)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)

    def canvasMoveEvent(self, e):
        #if e.button() == Qt.LeftButton:
        self.picked.emit(e.mapPoint(), False)

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.picked.emit(e.mapPoint(), True)

    def canvasReleaseEvent(self, e):
        pass



class CrayfishPlotWidget(QWidget):

    def __init__(self, layer, parent=None):
        QWidget.__init__(self, parent)

        self.layer = layer
        self.tool = PickGeometryTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)

        iface.mapCanvas().setMapTool(self.tool)

        self.gw = pyqtgraph.GraphicsWindow()
        self.plot = self.gw.addPlot()
        self.plot.showGrid(x=True, y=True)

        l = QVBoxLayout()
        l.addWidget(self.gw)
        self.setLayout(l)

    def on_picked(self, pt, clicked):

        x, y = timeseries_plot_data(self.layer, QgsGeometry.fromPoint(pt))

        self.plot.clear()
        #self.plot.setWindowTitle('Time Series')
        self.plot.getAxis('bottom').setLabel('Time [h]')
        self.plot.getAxis('left').setLabel(self.layer.currentDataSet().name())

        if not all(map(math.isnan, y)):
            pen = pyqtgraph.mkPen(color=(255,0,0), width=2, cosmetic=True)
            self.plot.plot(x=x, y=y, connect='finite', pen=pen)

        if clicked:  # no more updates if clicked
            # TODO: show marker on this position
            iface.mapCanvas().unsetMapTool(self.tool)

