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

from qgis.core import (
    QgsMapLayerStyle,
    QgsFillSymbolV2,
    QgsSingleSymbolRendererV2,
    QgsVectorGradientColorRampV2,
    QgsRendererCategoryV2,
    QgsCategorizedSymbolRendererV2,
    QgsGraduatedSymbolRendererV2,
    QgsRendererRangeV2
)

from PyQt4.QtGui import QColor

def style_with_black_lines(layer):
    symbols = layer.rendererV2().symbols()
    symbol = symbols[0]
    symbol.setColor(QColor(0, 0, 0))

def classified_style_from_colormap(layer, cm):
    assert(cm and layer)

    last_index = cm.item_count() - 1
    assert(last_index > 0) # at least 2 values

    cl = []
    for i in range(1, cm.item_count()): # skip first one
        item = cm.item(i)
        prev_item = cm.item(i-1)
        label = prev_item.label + " - " + item.label

        val = round(prev_item.value) # for some reason values are rounded to int

        sym = QgsFillSymbolV2.createSimple({})
        sym.setColor(QColor(*item.color))
        cat = QgsRendererCategoryV2(val, sym, label)
        cl.append(cat)

    renderer = QgsCategorizedSymbolRendererV2("CVAL", cl)
    layer.setRendererV2(renderer)

def classified_style_from_interval(layer, cm):
    def ramp_value(first_cm, last_cm, prev_item):
        if prev_item < first_cm.value:
           ramp_val = 0
        elif prev_item > last_cm.value:
           ramp_val = 1
        else:
           ramp_val = (prev_item - first_cm.value) / (last_cm.value - first_cm.value)
        return ramp_val

    assert(layer)
    last_index = cm.item_count() - 1
    assert(last_index > 0) # at least 2 values
    first_cm = cm.item(0)
    last_cm = cm.item(last_index)


    idx = layer.pendingFields().indexFromName("CVAL")
    vals = layer.uniqueValues(idx)
    ramp = QgsVectorGradientColorRampV2(QColor(*first_cm.color), QColor(*last_cm.color))

    cl = []
    for i in range(1, len(vals)): # skip first one
        item = vals[i]
        prev_item = vals[i-1]
        label = str(item) + " - " + str(prev_item)
        ramp_val = ramp_value(first_cm, last_cm, prev_item)
        val = round(prev_item) # for some reason values are rounded to int
        sym = QgsFillSymbolV2.createSimple({})
        sym.setColor(ramp.color(ramp_val))
        cat = QgsRendererCategoryV2(val, sym, label)
        cl.append(cat)

    renderer = QgsCategorizedSymbolRendererV2("CVAL", cl)
    layer.setRendererV2(renderer)
