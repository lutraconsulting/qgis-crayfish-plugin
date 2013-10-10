#!/usr/bin/env python
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

import sys
import os
import shutil
import platform
import glob

qgis1 = False

if len(sys.argv) > 1:
  for arg in sys.argv[1:]:
    if arg == '-1':
      qgis1 = True
    else:
      print "install.py [-1]"
      print ""
      print "  Install Crayfish Python plugin"
      print ""
      print "  Arguments:"
      print "  -1        Install to QGIS 1.x directory (instead of QGIS 2.x)"
      sys.exit(0)

qgis_folder = ".qgis" if qgis1 else ".qgis2"

plugin_dir = os.path.expanduser(os.path.join("~", qgis_folder, "python", "plugins", "crayfish"))

if not os.path.exists(plugin_dir):
  os.makedirs(plugin_dir)

install_files = ['metadata.txt'] + glob.glob("*.py") + glob.glob("*.png")
install_files.remove("install.py")  # exclude this file!

for filename in install_files:
  print "-- "+filename
  shutil.copy(filename, plugin_dir)
