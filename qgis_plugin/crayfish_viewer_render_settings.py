# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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

        # Live settings

        self.ds = ds

        self.shaftLength = ds.vectorShaftLengthMethod()
        self.shaftLengthMin = ds.vectorShaftLengthMin()
        self.shaftLengthMax = ds.vectorShaftLengthMax()
        self.shaftLengthFixedLength = ds.vectorShaftLengthFixed()
        self.shaftLengthScale = ds.vectorShaftLengthScaleFactor()

        self.lineWidth = ds.vectorPenWidth()

        self.headWidth = ds.vectorHeadWidth()
        self.headLength = ds.vectorHeadLength()


        self.displayVectorsOnGrid = False
        self.xSpacing = 50.0
        self.ySpacing = 50.0
        
        self.filterByMag = False
        self.minMag = 0.0
        self.maxMag = 100.0
        
        # Saved settings
        
        self.__shaftLength = None
        self.__shaftLengthMin = None
        self.__shaftLengthMax = None
        self.__shaftLengthFixedLength = None
        self.__shaftLengthScale = None
        
        self.__lineWidth = None
        
        self.__displayVectorsOnGrid = None
        self.__xSpacing = None
        self.__ySpacing = None
        
        self.__headWidth = None
        self.__headLength = None
        
        self.__filterByMag = None
        self.__minMag = None
        self.__maxMag = None
        
        
    def save(self):
        
        self.__shaftLength = self.shaftLength
        self.__shaftLengthMin = self.shaftLengthMin
        self.__shaftLengthMax = self.shaftLengthMax
        self.__shaftLengthFixedLength = self.shaftLengthFixedLength
        self.__shaftLengthScale = self.shaftLengthScale
        
        self.__lineWidth = self.lineWidth
        
        self.__displayVectorsOnGrid = self.displayVectorsOnGrid
        self.__xSpacing = self.xSpacing
        self.__ySpacing = self.ySpacing
        
        self.__headWidth = self.headWidth
        self.__headLength = self.headLength
        
        self.__filterByMag = self.filterByMag
        self.__minMag = self.minMag
        self.__maxMag = self.maxMag
        
        
    def restore(self):
        
        self.shaftLength = self.__shaftLength
        self.shaftLengthMin = self.__shaftLengthMin
        self.shaftLengthMax = self.__shaftLengthMax
        self.shaftLengthFixedLength = self.__shaftLengthFixedLength
        self.shaftLengthScale = self.__shaftLengthScale
        
        self.lineWidth = self.__lineWidth
        
        self.displayVectorsOnGrid = self.__displayVectorsOnGrid
        self.xSpacing = self.__xSpacing
        self.ySpacing = self.__ySpacing
        
        self.headWidth = self.__headWidth
        self.headLength = self.__headLength
        
        self.filterByMag = self.__filterByMag
        self.minMag = self.__minMag
        self.maxMag = self.__maxMag

        self.applyToDataSet()

    def applyToDataSet(self):

        self.ds.setVectorShaftLengthMethod(self.shaftLength)  # Method used to scale the shaft (sounds rude doesn't it)
        self.ds.setVectorShaftLengthMinMax(self.shaftLengthMin, self.shaftLengthMax)
        self.ds.setVectorShaftLengthScaleFactor(self.shaftLengthScale)
        self.ds.setVectorShaftLengthFixed(self.shaftLengthFixedLength)
        self.ds.setVectorPenWidth(self.lineWidth)
        self.ds.setVectorHeadSize(self.headWidth, self.headLength)
