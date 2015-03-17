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

class CrayfishViewerRenderSettings():
    
    def __init__(self, ds):
        """
            Set defaults
        """

        self.ds = ds

        self.shaftLength = ds.config["v_shaft_length_method"]
        self.shaftLengthMin = ds.config["v_shaft_length_min"]
        self.shaftLengthMax = ds.config["v_shaft_length_max"]
        self.shaftLengthFixedLength = ds.config["v_shaft_length_fixed"]
        self.shaftLengthScale = ds.config["v_shaft_length_scale"]

        self.lineWidth = ds.config["v_pen_width"]

        self.headWidth = ds.config["v_head_width"]
        self.headLength = ds.config["v_head_length"]

        # unused stuff

        self.displayVectorsOnGrid = False
        self.xSpacing = 50.0
        self.ySpacing = 50.0
        
        self.filterByMag = False
        self.minMag = 0.0
        self.maxMag = 100.0


    def applyToDataSet(self):

        self.ds.config["v_shaft_length_method"] = self.shaftLength  # Method used to scale the shaft (sounds rude doesn't it)
        self.ds.config["v_shaft_length_min"] = self.shaftLengthMin
        self.ds.config["v_shaft_length_max"] = self.shaftLengthMax
        self.ds.config["v_shaft_length_scale"] = self.shaftLengthScale
        self.ds.config["v_shaft_length_fixed"] = self.shaftLengthFixedLength
        self.ds.config["v_pen_width"] = self.lineWidth
        self.ds.config["v_head_width"] = self.headWidth
        self.ds.config["v_head_length"] = self.headLength

