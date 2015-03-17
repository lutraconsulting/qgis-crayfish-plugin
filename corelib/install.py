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

debug = False
qgis1 = False
pkg = False
win = platform.system() == 'Windows'
file_cpp = "crayfish.dll" if win else "libcrayfish.so.1"

if len(sys.argv) > 1:
  for arg in sys.argv[1:]:
    if arg == '-debug':
      debug = True
    elif arg == '-1':
      qgis1 = True
    elif arg == '-pkg':
      pkg = True
    else:
      print "install.py [-debug] [-1] [-pkg]"
      print ""
      print "  Install Crayfish C++ library"
      print ""
      print "  Arguments:"
      print "  -debug    Use debug version of Crayfish C++ library"
      print "  -1        Install to QGIS 1.x directory (instead of QGIS 2.x)"
      print "  -pkg      Create .zip package for distribution instead of installation"
      sys.exit(0)

build_mode = "debug" if debug else "release"
build_file_cpp = os.path.join("build", build_mode, file_cpp)

if pkg:
  import zipfile
  with zipfile.ZipFile("crayfish_viewer_library.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write(build_file_cpp, file_cpp)
  print "Written crayfish_viewer_library.zip"

else:
  qgis_folder = ".qgis" if qgis1 else ".qgis2"
  plugin_dir = os.path.expanduser(os.path.join("~", qgis_folder, "python", "plugins", "crayfish"))
  
  if not os.path.exists(plugin_dir):
    os.makedirs(plugin_dir)

  shutil.copy(build_file_cpp, plugin_dir)
  print "Written " + ("[debug] " if debug else "") + file_cpp + " to " + plugin_dir

