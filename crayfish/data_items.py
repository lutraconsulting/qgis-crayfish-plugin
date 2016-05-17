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

from PyQt4.QtGui import QIcon
from qgis.core import *

class CrayfishDataItemProvider(QgsDataItemProvider):

  # TODO: .nc cannot be loaded simply from browser as is because it loads multiple layers
  extensions = [".2dm", ".sww", ".grib", ".grib1", ".grib2", ".bin", ".grb", ".hdf", ".slf", "BASE.OUT"]

  icon = QIcon(":/plugins/crayfish/crayfish.png")

  def name(self):
    return "Crayfish"

  def capabilities(self):
    return 1 # QgsDataProvider.File

  def createDataItem(self, path, parentItem):
    if not self._supported_extension(path):
      return None

    base = os.path.basename(path)
    item = QgsLayerItem(parentItem, base, path, path, QgsLayerItem.Plugin, "crayfish_viewer")
    item.setState(QgsDataItem.Populated) # make it non-expandable
    item.setIcon(self.icon)
    return item

  def _supported_extension(self, path):
    for ext in self.extensions:
      if path.endswith(ext):
        return True
    return False
