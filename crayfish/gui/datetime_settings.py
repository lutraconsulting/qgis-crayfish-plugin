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

import datetime


class CrayfishDateTimeSettings():
    
    def __init__(self, ds):
        """
            Set defaults
        """
        self.ds = ds

        self.useAbsoluteTime = ds.timeConfig["dt_use_absolute_time"]

        self.subtractHours = ds.timeConfig["dt_subtract_hours"]
        self.timeFormat = ds.timeConfig["dt_time_format"]

        self.refTime = ds.timeConfig["dt_reference_time"]
        self.dateTimeFormat = ds.timeConfig["dt_datetime_format"]

    def dataSet(self):
        return self.ds

    def apply_to_dataset(self):
        self.ds.timeConfig["dt_use_absolute_time"] = self.useAbsoluteTime

        self.ds.timeConfig["dt_subtract_hours"] = self.subtractHours
        self.ds.timeConfig["dt_time_format"] = self.timeFormat

        self.ds.timeConfig["dt_reference_time"] = self.refTime
        self.ds.timeConfig["dt_datetime_format"] = self.dateTimeFormat
