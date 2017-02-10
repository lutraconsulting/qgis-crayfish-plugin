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

class CrayfishDateTimeSettings():
    
    def __init__(self, ds):
        """
            Set defaults
        """
        self.ds = ds

        self.substractHours = ds.config["datetime_substract_hours"]
        self.useAbsoluteTime = ds.config["datetime_use_absolute_time"]
        self.refTime = ds.config["datetime_reference_time"]
        self.absoluteTimeFormat = ds.config["datetime_absolute_time_format"]

    def applyToDataSet(self):
        self.ds.config["datetime_substract_hours"] = self.substractHours
        self.ds.config["datetime_use_absolute_time"] = self.useAbsoluteTime
        self.ds.config["datetime_reference_time"] = self.refTime
        self.ds.config["datetime_absolute_time_format"] = self.absoluteTimeFormat
