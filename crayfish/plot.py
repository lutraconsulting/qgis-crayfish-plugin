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
from qgis.core import *

from PyQt5.Qt import PYQT_VERSION_STR

try:
    import pyqtgraph as pg
    from pyqtgraph.exporters import ImageExporter
except ImportError:
    import crayfish.pyqtgraph_0_12_2 as pg
    from crayfish.pyqtgraph_0_12_2.exporters import ImageExporter

from .utils import integrate

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

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
def check_if_PyQt_version_is_before(M,m,r):
    strVersion=PYQT_VERSION_STR
    num=strVersion.split('.')
    numM=int(num[0])
    numm = int(num[1])
    numr = int(num[2])
    return  numM < M or (numM == M and numm < m) or (numM == M and numm < m and numr < r)


# see https://github.com/pyqtgraph/pyqtgraph/issues/1057
pyqtGraphAcceptNaN = check_if_PyQt_version_is_before(5, 13, 1)

def timeseries_plot_data(layer, ds_group_index, geometry, searchradius=0):
    """ return array with tuples defining X,Y points for plot """
    x,y = [], []
    if not layer:
        return x, y

    pt = geometry.asPoint()
    for i in range(layer.dataProvider().datasetCount(ds_group_index)):
        meta = layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(ds_group_index, i))
        t = meta.time()
        dataset = QgsMeshDatasetIndex(ds_group_index, i)
        value = layer.datasetValue(dataset, pt,searchradius).scalar()
        if not pyqtGraphAcceptNaN and math.isnan(value):
            value=0;

        x.append(t)
        y.append(value)

    return x, y


def cross_section_plot_data(layer, ds_group_index, ds_index, geometry, resolution=1.):
    """ return array with tuples defining X,Y points for plot """
    x,y = [], []
    if not layer:
        return x, y

    dataset = QgsMeshDatasetIndex(ds_group_index, ds_index)
    offset = 0
    length = geometry.length()
    while offset < length:
        pt = geometry.interpolate(offset).asPoint()
        value = layer.datasetValue(dataset, pt).scalar()
        if not pyqtGraphAcceptNaN and math.isnan(value):
            value = 0
        x.append(offset)
        y.append(value)
        offset += resolution

    # let's make sure we include also the last point
    last_pt = geometry.asPolyline()[-1]
    last_value = layer.datasetValue(dataset, last_pt).scalar()

    if not pyqtGraphAcceptNaN and math.isnan(last_value):
        last_value = 0

    x.append(length)
    y.append(last_value)

    return x,y

def integral_plot_data(layer, ds_group_index, geometry, resolution=1.):
    """ return array with tuples defining X,Y points for plot """
    x, y = [], []
    if not layer:
        return x, y

    for i in range(layer.dataProvider().datasetCount(ds_group_index)):
        meta = layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(ds_group_index, i))
        t = meta.time()
        cs_x, cs_y = cross_section_plot_data(layer, ds_group_index, i, geometry, resolution)
        value = integrate(cs_x, cs_y)
        x.append(t)
        y.append(value)

    return x, y

def profile_1D_plot_data(layer, dataset_group_index, dataset_index,profile):
    """ return array with tuples defining X,Y points for plot """
    x, y = [], []
    if not layer or len(profile)<2:
        return x, y

    groupMeta = layer.dataProvider().datasetGroupMetadata(dataset_group_index)
    isOnVertices = groupMeta.dataType() == QgsMeshDatasetGroupMetadata.DataOnVertices
    layerDataSetIndex = QgsMeshDatasetIndex(dataset_group_index,dataset_index)

    totalLength=0
    #append first x,y if on vertices
    p1 = profile[0]
    p2 = profile[1]
    length = p1.distance(p2)
    searchRadius=length/100
    if isOnVertices:
        x.append(0)
        y.append(layer.dataset1dValue(layerDataSetIndex,p1,searchRadius).scalar())
        totalLength=length


    for i in range(len(profile)-1):
        p1 = profile[i]
        p2 = profile[i+1]
        length = p1.distance(p2)
        searchRadius = length / 100
        if isOnVertices:
            x.append(totalLength+length)
            y.append(layer.dataset1dValue(layerDataSetIndex, p2, searchRadius).scalar())
        else:
            x.append(totalLength + length/2)
            midPoint=QgsPointXY((p1.x()+p2.x())/2 , (p1.y()+p2.y())/2)
            y.append(layer.dataset1dValue(layerDataSetIndex,midPoint,searchRadius).scalar())

        totalLength=totalLength+length

    return x, y


def show_plot(*args, **kwargs):
    """ Open a new window with a plot and return the plot widget.
    Just a wrapper around pyqtgraph's plot() method """
    return pg.plot(*args, **kwargs)


def export_plot(plt, filename, width=None, height=None):
    """ Export an existing plot to an image and save with given filename.
    Optionally, image width and height in pixels can be specified. """
    e = ImageExporter(plt.plotItem)
    if width is not None: e.parameters()['width'] = width
    if height is not None: e.parameters()['height'] = height
    e.export(filename)


def plot_3d_data(layer, ds_group_index, ds_dataset_index, geom_pt):
    """ return array with tuples defining X,Y points for plot """
    average = None
    x,y = [], []
    if not layer:
        return x, y, average

    ds = QgsMeshDatasetIndex(ds_group_index, ds_dataset_index)
    pt = geom_pt.asPoint()
    block = layer.dataset3dValue(ds, pt)
    if block.isValid():
        nvols = block.volumesCount()
        extrusions = block.verticalLevels()

        for i in range(nvols):
            ext = extrusions[i] + ( extrusions[i+1] - extrusions[i] ) / 2.0
            val = block.value(i).scalar()
            x.append(val)
            y.append(ext)

        averageVal = layer.datasetValue(ds, pt)
        average = averageVal.scalar()

    return x, y, average
