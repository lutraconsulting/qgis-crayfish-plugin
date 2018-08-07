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
import datetime
import math

import qgis.core
import qgis.gui

from qgis.PyQt import *


from qgis.gui import QgsCollapsibleGroupBox


from qgis.gui import QgsMessageBar
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

def time_to_string(time, ds=None):  # time is in hours
    #  TODO remove None
    # maybe would be worth to put this as direct replacement of output.time()...
    if ds and ds.timeConfig:
        if ds.timeConfig["dt_use_absolute_time"]:
            res = ds.timeConfig["dt_reference_time"] + datetime.timedelta(hours=time)
            return res.strftime(ds.timeConfig["dt_datetime_format"])
        else:
            hours = time + ds.timeConfig["dt_offset_hours"]
            if ds.timeConfig["dt_time_format"] == "%H:%M:%S":
                return _hours_to_HHMMSS(hours)
            elif ds.timeConfig["dt_time_format"] == "%d %H:%M:%S":
                seconds = round(hours * 3600.0, 2)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                d, h = divmod(hours, 24)
                return "%02d %02d:%02d:%05.2f" % (d, h, m, s)
            elif ds.timeConfig["dt_time_format"] == "%d %H":
                d, h = divmod(hours, 24)
                return "%02d %05.3f" % (d, h)
            elif ds.timeConfig["dt_time_format"] == "%d":
                return "%06.3f" % (hours / 24.)
            elif ds.timeConfig["dt_time_format"] == "%H":
                return "%06.3f" % hours
            elif ds.timeConfig["dt_time_format"] == "%S":
                return "%9i" % round(hours * 3600)
            else:
                assert(False) # should never happen
    else:
        return _hours_to_HHMMSS(time)

def load_ui(name):
    ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'ui',
                          name + '.ui')
    return uic.loadUiType(ui_file)
