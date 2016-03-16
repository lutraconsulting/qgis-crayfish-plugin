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
from crayfish_gui_utils import QgsMessageBar, qgis_message_bar, defaultColorRamp
from qgis.utils import iface

import crayfish

import os
import glob


class CrayfishViewerPluginLayerRenderer(QgsMapLayerRenderer):
    def __init__(self, layer, rendererContext):

        QgsMapLayerRenderer.__init__(self, layer.id())

        self.layer = layer
        self.rconfig = self._create_rconfig()
        self.rendererContext = rendererContext

        self._set_destination_crs()

    def _create_rconfig(self):
        rconfig = crayfish.RendererConfig()
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

        return rconfig

    def _set_destination_crs(self):
        ct = self.rendererContext.coordinateTransform()
        self.layer.mesh.set_destination_crs(ct.destCRS().toProj4() if ct else None)

    def render(self):
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
        width = (bottomright.x() - topleft.x())
        height = (bottomright.y() - topleft.y())

        rconfig.set_view((int(width),int(height)), (extent.xMinimum(), extent.yMinimum()), pixelSize)

        if False:
            print '\n'
            print 'About to render with the following parameters:'
            print '\tExtent:\t%f,%f - %f,%f\n' % (extent.xMinimum(),extent.yMinimum(),extent.xMaximum(),extent.yMaximum())
            print '\tWidth:\t' + str(width) + '\n'
            print '\tHeight:\t' + str(height) + '\n'
            print '\tXMin:\t' + str(extent.xMinimum()) + '\n'
            print '\tYMin:\t' + str(extent.yMinimum()) + '\n'
            print '\tPixSz:\t' + str(pixelSize) + '\n'

        img = QImage(width,height, QImage.Format_ARGB32)
        img.fill(0)

        r = crayfish.Renderer(self.rconfig, img)
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
