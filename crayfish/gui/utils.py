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

import os
from qgis.core import *
from qgis.PyQt import uic
from qgis.utils import iface
qgis_message_bar = iface.messageBar()

def float_safe(txt):
    """ convert to float, return 0 if conversion is not possible """
    try:
        return float(txt)
    except ValueError:
        return 0.


def _hours_to_HHMMSS(hours):
    seconds = round(hours * 3600.0, 2)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%05.2f" % (h, m, s)


def time_to_string(time):  # time is in hours
    # TODO time formatting!
    return _hours_to_HHMMSS(time)


def mesh_layer_active_dataset_group_with_maximum_timesteps(layer):
    """ returns active dataset group with maximum datasets and the number of datasets """
    group_index = None
    timesteps = 0

    if layer and layer.dataProvider() and layer.type() == QgsMapLayer.MeshLayer:
        rendererSettings = layer.rendererSettings()
        asd = rendererSettings.activeScalarDataset()

        if asd.isValid():
            group_index = asd.group()
            timesteps = layer.dataProvider().datasetCount(asd.group())

        avd = rendererSettings.activeVectorDataset()
        if avd.isValid():
            avd_timesteps = layer.dataProvider().datasetCount(avd.group())
            if avd_timesteps > timesteps:
                group_index = avd.group()

    return group_index

def load_ui(name):
    ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'ui',
                          name + '.ui')
    return uic.loadUiType(ui_file)
