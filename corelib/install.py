#!/usr/bin/env python
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

import sys
import os
import shutil
import platform

pkg = False
win = platform.system() == 'Windows'
file_cpp = "crayfish.dll" if win else "libcrayfish.so.1"

if len(sys.argv) > 1:
  for arg in sys.argv[1:]:
    if arg.startswith('-pkg='):
      pkg = True
      version = arg[5:]
    else:
      print "install.py [-pkg=version]"
      print ""
      print "  Install Crayfish C++ library"
      print ""
      print "  Arguments:"
      print "  -pkg      Create .zip package for distribution instead of installation"
      sys.exit(0)

build_file_cpp = os.path.join("..", "plugin", file_cpp)

if pkg:
  zipfilename = "crayfish-lib-%s.zip" % version
  import zipfile
  with zipfile.ZipFile(os.path.join("..", zipfilename), "w", zipfile.ZIP_DEFLATED) as z:
    z.write(build_file_cpp, file_cpp)
  print "Written " + zipfilename

else:
  plugin_dir = os.path.expanduser(os.path.join("~", ".qgis2", "python", "plugins", "crayfish"))
  
  if not os.path.exists(plugin_dir):
    os.makedirs(plugin_dir)

  shutil.copy(build_file_cpp, plugin_dir)
  print "Written " + file_cpp + " to " + plugin_dir

