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

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication
from qgis.core import QgsProcessingAlgorithm

from .cf_error import CrayfishProccessingAlgorithmError


class CfGeoAlgorithm(QgsProcessingAlgorithm):

    def createInstance(self):
        return type(self)()

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")


def trAlgorithm(self, string, context=''):
    """Implementation of GeoAlgorithm.trAlgorithm() for older versions of QGIS (e.g. 2.8)"""
    if context == '':
        context = self.__class__.__name__
    return string, QCoreApplication.translate(context, string)

# patch our derived class
if not hasattr(CfGeoAlgorithm, "trAlgorithm"):
    setattr(CfGeoAlgorithm, "trAlgorithm", trAlgorithm)
