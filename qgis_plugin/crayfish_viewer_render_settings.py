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

        self.shaftLength = ds.vectorShaftLengthMethod()
        self.shaftLengthMin = ds.vectorShaftLengthMin()
        self.shaftLengthMax = ds.vectorShaftLengthMax()
        self.shaftLengthFixedLength = ds.vectorShaftLengthFixed()
        self.shaftLengthScale = ds.vectorShaftLengthScaleFactor()

        self.lineWidth = ds.vectorPenWidth()

        self.headWidth = ds.vectorHeadWidth()
        self.headLength = ds.vectorHeadLength()

        # unused stuff

        self.displayVectorsOnGrid = False
        self.xSpacing = 50.0
        self.ySpacing = 50.0
        
        self.filterByMag = False
        self.minMag = 0.0
        self.maxMag = 100.0


    def applyToDataSet(self):

        self.ds.setVectorShaftLengthMethod(self.shaftLength)  # Method used to scale the shaft (sounds rude doesn't it)
        self.ds.setVectorShaftLengthMinMax(self.shaftLengthMin, self.shaftLengthMax)
        self.ds.setVectorShaftLengthScaleFactor(self.shaftLengthScale)
        self.ds.setVectorShaftLengthFixed(self.shaftLengthFixedLength)
        self.ds.setVectorPenWidth(self.lineWidth)
        self.ds.setVectorHeadSize(self.headWidth, self.headLength)

