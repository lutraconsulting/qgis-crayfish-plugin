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
from qgis.core import *
from qgis.utils import iface

from .core import Renderer, RendererConfig


class CrayfishViewerPluginLayerRenderer(QgsMapLayerRenderer):
    def __init__(self, layer, rendererContext):

        QgsMapLayerRenderer.__init__(self, layer.id())

        self.layer = layer
        self.rendererContext = rendererContext

        # Now extract all relevant information from the layer settings for rendering
        self._calculate_extent()
        self._create_rconfig()

        # And notify corelib to reproject if needed
        self._set_destination_crs()

    def _calculate_extent(self):
        mapToPixel = self.rendererContext.mapToPixel()
        pixelSize = mapToPixel.mapUnitsPerPixel()
        ct = self.rendererContext.coordinateTransform()
        extent = self.rendererContext.extent()  # this is extent in layer's coordinate system - but we need
        if ct:
          # TODO: need a proper way how to get visible extent without using map canvas from interface
          if iface.mapCanvas().isDrawing():
            extent = iface.mapCanvas().extent()
          else:
            extent = ct.transformBoundingBox(extent)  # TODO: this is just approximate :-(
        topleft = mapToPixel.transform(extent.xMinimum(), extent.yMaximum())
        bottomright = mapToPixel.transform(extent.xMaximum(), extent.yMinimum())

        self.pixelSize = pixelSize
        self.width = (bottomright.x() - topleft.x())
        self.height = (bottomright.y() - topleft.y())
        self.extent = extent

    def _create_rconfig(self):
        rconfig = RendererConfig()
        rconfig.set_output_mesh(self.layer.mesh)

        dsC = self.layer.currentContourDataSet()
        if dsC:
          rconfig.set_output_contour(self.layer.currentContourOutput())
          for k,v in dsC.config.iteritems():
            if k.startswith("c_"):
              rconfig[k] = v

        dsV = self.layer.currentVectorDataSet()
        if dsV:
          rconfig.set_output_vector(self.layer.currentVectorOutput())
          for k,v in dsV.config.iteritems():
            if k.startswith("v_"):
              rconfig[k] = v

        for k,v in self.layer.config.iteritems():
          rconfig[k] = v

        rconfig.set_view((int(self.width),int(self.height)), (self.extent.xMinimum(), self.extent.yMinimum()), self.pixelSize)
        self.rconfig = rconfig

    def _set_destination_crs(self):
        # Set in main thread, so the mesh projection arrays
        # are populated correctly before used for example by identify tools
        ct = self.rendererContext.coordinateTransform()
        self.layer.mesh.set_destination_crs(ct.destCRS().toProj4() if ct else None)

    def _print_debug_info(self):
            print '\n'
            print 'About to render with the following parameters:'
            print '\tExtent:\t%f,%f - %f,%f' % (self.extent.xMinimum(), self.extent.yMinimum(), self.extent.xMaximum(), self.extent.yMaximum())
            print '\tWidth:\t' + str(self.width)
            print '\tHeight:\t' + str(self.height)
            print '\tXMin:\t' + str(self.extent.xMinimum())
            print '\tYMin:\t' + str(self.extent.yMinimum())
            print '\tPixSz:\t' + str(self.pixelSize)

    def render(self):
        # This is done in separate rendering thread
        if False:
            self._print_debug_info()

        img = QImage(self.width, self.height, QImage.Format_ARGB32)
        img.fill(0)

        r = Renderer(self.rconfig, img)
        r.draw()

        # img now contains the render of the crayfish layer, merge it

        painter = self.rendererContext.painter()
        rasterScaleFactor = self.rendererContext.rasterScaleFactor()
        invRasterScaleFactor = 1.0/rasterScaleFactor
        painter.save()
        painter.scale(invRasterScaleFactor, invRasterScaleFactor)
        painter.drawImage(0, 0, img)
        painter.restore()
        return True
