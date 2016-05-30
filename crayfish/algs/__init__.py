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

from PyQt4.QtGui import *

from processing.core.AlgorithmProvider import AlgorithmProvider

from .cf_info import InfoAlgorithm
from .cf_export_elems import ExportMeshElemsAlgorithm
from .cf_export_grid import ExportMeshGridAlgorithm

class CrayfishProcessingProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        # Deactivate provider by default
        self.activate = False

        # Load algorithms
        self.alglist = [InfoAlgorithm(),
                        ExportMeshElemsAlgorithm(),
                        ExportMeshGridAlgorithm()]

        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'Crayfish provider'

    def getDescription(self):
        return 'Crayfish algorithms'

    def getIcon(self):
        return QIcon(":/plugins/crayfish/crayfish.png")

    def _loadAlgorithms(self):
        self.algs = self.alglist
