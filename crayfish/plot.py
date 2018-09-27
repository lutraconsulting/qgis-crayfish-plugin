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

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from qgis.core import *

from . import pyqtgraph as pg
from .pyqtgraph.exporters import ImageExporter

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

def timeseries_plot_data(layer, ds_group_index, geometry):
    """ return array with tuples defining X,Y points for plot """
    x,y = [], []
    if not layer:
        return x, y

    pt = geometry.asPoint()
    for i in range(layer.dataProvider().datasetCount(ds_group_index)):
        meta = layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(ds_group_index, i))
        t = meta.time()
        dataset = QgsMeshDatasetIndex(ds_group_index, i)
        value = layer.datasetValue(dataset, pt).scalar()
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
        x.append(offset)
        y.append(value)
        offset += resolution

    # let's make sure we include also the last point
    last_pt = geometry.asPolyline()[-1]
    last_value = layer.datasetValue(dataset, last_pt).scalar()
    x.append(length)
    y.append(last_value)

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
