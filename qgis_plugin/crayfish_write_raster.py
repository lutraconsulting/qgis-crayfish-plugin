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

from osgeo import gdal
import numpy

from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import QImage, qRed, qGreen, qBlue, qAlpha


def renderToRaster(layer, fileName, imgW, extent=None):
  """ Render Crayfish plugin layer with its current settings to a raster file.
  Only image width is needed - height is computed from extent aspect ratio.
  Uses mesh extent if extent is not specified.
  """

  if extent is None:
    extent = layer.provider.meshExtent()

  dX = extent.right()-extent.left()
  dY = extent.bottom()-extent.top()
  imgH = int(imgW * dY/dX)
  mupp = dX / imgW

  oldSize = layer.provider.canvasSize()
  oldExtent = layer.provider.extent()
  oldPixelSize = layer.provider.pixelSize()

  layer.provider.setCanvasSize(QSize(imgW,imgH))
  layer.provider.setExtent(extent.left(), extent.top(), mupp)
  img = layer.provider.draw()

  crsWkt = layer.crs().toWkt()
  qimageToRaster(img, fileName, extent.left(), extent.bottom(), mupp, crsWkt)

  layer.provider.setCanvasSize(oldSize)
  layer.provider.setExtent(oldExtent.left(), oldExtent.top(), oldPixelSize)


def qimageToRaster(img, fileName, xMin=0, yMax=0, mupp=1, crsWkt=None):
  """ Use GDAL to turn a QImage to GeoTIFF file """

  driver = gdal.GetDriverByName("GTiff")

  ds = driver.Create(fileName, img.width(), img.height(), 4, gdal.GDT_Byte, ['ALPHA=YES'])

  # setup affine transform
  ds.SetGeoTransform([ xMin, mupp, 0, yMax, 0, -mupp ])

  if crsWkt is not None:
    ds.SetProjection(str(crsWkt))

  size = img.height(), img.width()
  raster_r = numpy.zeros(size, dtype=numpy.uint8)
  raster_g = numpy.zeros(size, dtype=numpy.uint8)
  raster_b = numpy.zeros(size, dtype=numpy.uint8)
  raster_a = numpy.zeros(size, dtype=numpy.uint8)

  for i in xrange(img.width()*img.height()):
    x,y = i % img.width(), i / img.width()
    rgb = img.pixel(x,y)
    raster_r[y,x], raster_g[y,x], raster_b[y,x], raster_a[y,x] = qRed(rgb), qGreen(rgb), qBlue(rgb), qAlpha(rgb)

  ds.GetRasterBand(1).WriteArray(raster_r)
  ds.GetRasterBand(2).WriteArray(raster_g)
  ds.GetRasterBand(3).WriteArray(raster_b)
  ds.GetRasterBand(4).WriteArray(raster_a)

  ds = None   # Once we're done, close properly the dataset
