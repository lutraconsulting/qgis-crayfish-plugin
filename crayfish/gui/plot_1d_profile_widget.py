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

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import math

from qgis._core import QgsPointXY
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface

from .plot_map_layer_widget import MapLayersWidget


class PickProfileTool(QgsMapTool):

    picked = pyqtSignal(QgsPointXY, bool, bool)   # list of vertex index, whether finished or still drawing

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.points = []
        self.capturing = False


    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.picked.emit(e.mapPoint(), False, e.modifiers() & Qt.ControlModifier)
            self.capturing = True
        if e.button() == Qt.RightButton:
            self.picked.emit(e.mapPoint(), True, False)
            self.capturing = False

    def canvasReleaseEvent(self, e):
        pass


class Profile1DPickerWidget(QToolButton):

    geometry_changed = pyqtSignal()

    PICK_NO, PICK_MAP, PICK_LAYER = range(3)

    def __init__(self, parent=None):
        QToolButton.__init__(self, parent)

        self.setToolTip("Select point to define a longitudinal profile (ctrl for intermediate point) ")

        self.setText("Select profile from map")
        self.setCheckable(True)
        self.clicked.connect(self.picker_clicked)

        self.pick_mode = self.PICK_NO
        self.pick_layer = None

        self.vectorLayer = None
        self.meshLayer = None
        self.tracer = QgsTracer()
        self.tracer.setDestinationCrs(iface.mapCanvas().mapSettings().destinationCrs(),
                                      iface.mapCanvas().mapSettings().transformContext())
        self.temporaryTrace = []
        self.profileTrace = []

        self.firstVertex = QgsPointXY()
        self.firstVertexMarker = None
        self.profileHighlight = None

        self.tool = PickProfileTool(iface.mapCanvas())
        self.tool.picked.connect(self.on_picked)
        self.tool.setButton(self)

    def clear_geometries(self):
        self.firstVertex = QgsPointXY()
        self.temporaryTrace = []
        self.profileTrace = []
        self.clear_marker()
        self.geometry_changed.emit()

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

        self.profileTrace.extend(self.temporaryTrace)
        self.temporaryTrace = []
        self.firstVertex = QgsPointXY()

        self.updateMarker()

        self.pick_mode = self.PICK_NO

    def on_picked(self, point, finished, ctrl):
        if self.meshLayer is None:
            return

        if finished:  # no more updates
            self.stop_picking()
            return;

        searchradius=self.tool.searchRadiusMU(iface.mapCanvas())
        vertexMapPosition=self.meshLayer.snapOnVertex(point,searchradius)

        if not self.tracer.isPointSnapped(vertexMapPosition):
            return;

        if self.firstVertex.isEmpty():
            self.firstVertex = vertexMapPosition
        else:
            if ctrl:  # Intermediate point
                if len(self.profileTrace) == 0:
                    lastVertex = self.firstVertex
                else:
                    lastVertex = self.profileTrace[-1]
                newTrace = self.tracer.findShortestPath(lastVertex, vertexMapPosition)[0]
                newTrace.pop(0)
                self.profileTrace.extend(newTrace)
                self.firstVertex = vertexMapPosition
                self.temporaryTrace=[]
            else:
                self.temporaryTrace = self.tracer.findShortestPath(self.firstVertex, vertexMapPosition)[0]
                if not len(self.profileTrace) == 0:  # If a trace exists before the temporary one,
                    self.temporaryTrace.pop(0)       # remove the first element to avoid duplicate vertex

        self.updateMarker()

        self.geometry_changed.emit()

    def initializeTracer(self, meshLayer):

        self.meshLayer=meshLayer
        self.profileTrace = []
        self.newTrace = []

        if meshLayer is None:
            return

        mesh = QgsMesh()

        if meshLayer.dataProvider().contains(QgsMesh.Edge):
            meshLayer.dataProvider().populateMesh(mesh)

        self.vectorLayer = QgsVectorLayer("linestringZ", "meshLayer", "memory")
        self.vectorLayer.setCustomProperty("skipMemoryLayersCheck", 1)
        self.vectorLayer.setCrs(meshLayer.crs())
        self.vectorLayer.startEditing()

        field = QgsField("EdgeIndex", QVariant.Int)
        self.vectorLayer.addAttribute(field)

        edgeCount = mesh.edgeCount()
        for i in range(edgeCount):
            f = QgsFeature()
            edge = mesh.edge(i)
            p1 = mesh.vertex(edge[0])
            p2 = mesh.vertex(edge[1])
            line = QgsLineString(p1, p2)
            geometry = QgsGeometry(line)
            f.setGeometry(geometry)
            attrs = [i]
            f.setAttributes(attrs)
            self.vectorLayer.addFeature(f)

        self.vectorLayer.commitChanges()

        layers = [self.vectorLayer]
        self.tracer.setLayers(layers)
        self.tracer.init()

    def clear_marker(self):
        if self.firstVertexMarker is not None:
            iface.mapCanvas().scene().removeItem(self.firstVertexMarker)
            self.firstVertexMarker = None
        if self.profileHighlight is not None:
            iface.mapCanvas().scene().removeItem(self.profileHighlight)
            self.profileHighlight = None

    def updateMarker(self):
        self.clear_marker()
        if not self.firstVertex.isEmpty():
            self.firstVertexMarker = QgsVertexMarker(iface.mapCanvas())
            self.firstVertexMarker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            self.firstVertexMarker.setPenWidth(2)
            self.firstVertexMarker.setFillColor(QColor(150, 150, 0, 150))
            self.firstVertexMarker.setCenter(self.firstVertex)

        trace=self.profile()
        if len(trace) > 1:
            geometry = QgsGeometry.fromPolylineXY(trace)
            self.profileHighlight = QgsHighlight(iface.mapCanvas(), geometry, None)
            self.profileHighlight.setWidth(5)
            self.profileHighlight.setColor(QColor(255, 165, 0, 170))

    def profile(self):
        trace = self.profileTrace.copy()
        trace.extend(self.temporaryTrace)
        return trace
