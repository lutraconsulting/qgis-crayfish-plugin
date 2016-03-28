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

from __future__ import print_function
import sys
import os
import shutil
import platform
import glob

pkg = False

if len(sys.argv) > 1:
  for arg in sys.argv[1:]:
    if arg.startswith('-pkg='):
      pkg = True
      version = arg[5:]
    else:
      print("install.py [-pkg=version]")
      print("")
      print("  Install Crayfish Python plugin")
      print("")
      print("  Arguments:")
      print("  -pkg      Create a package for upload instead of installing")
      sys.exit(0)

install_files = ['metadata.txt']
install_files += glob.glob("*.py")
install_files += glob.glob("*.png")
install_files += glob.glob("gui/*.py")
install_files += glob.glob("illuvis/*.py")
install_files += glob.glob("doc/*")
install_files += glob.glob("ui/*")
install_files.remove("install.py")  # exclude this file!
install_dirs = ['illuvis', 'doc', 'ui', 'gui']

# add pyqtgraph
for entry in os.walk('pyqtgraph'):
  install_dirs.append(entry[0])
  for file_entry in entry[2]:
    install_files.append(os.path.join(entry[0], file_entry))

if pkg:
  import zipfile
  with zipfile.ZipFile(os.path.join("..","crayfish-%s.zip" % version), "w", zipfile.ZIP_DEFLATED) as z:
    for filename in install_files:
      z.write(filename, "crayfish/"+filename)

else:
  plugin_dir = os.path.expanduser(os.path.join("~", ".qgis2", "python", "plugins", "crayfish"))
  if not os.path.exists(plugin_dir):
    os.makedirs(plugin_dir)
  print(install_dirs)
  for subdir in install_dirs:
    subdir_path = os.path.join(plugin_dir, subdir)
    if not os.path.exists(subdir_path): os.makedirs(subdir_path)

  for filename in install_files:
    print("-- "+filename)
    destdir = os.path.join(plugin_dir, os.path.dirname(filename))
    shutil.copy(filename, destdir)
