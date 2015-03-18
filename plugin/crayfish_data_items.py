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

import os

from qgis.core import *

class CrayfishDataItemProvider(QgsDataItemProvider):

  def name(self):
    return "Crayfish"

  def capabilities(self):
    return 1 # QgsDataProvider.File

  def createDataItem(self, path, parentItem):
    if not path.endswith(".2dm"):
      return None

    base = os.path.basename(path)
    item = QgsLayerItem(parentItem, base, path, path, QgsLayerItem.Plugin, "crayfish_viewer")
    item.setState(QgsDataItem.Populated) # make it non-expandable
    return item
