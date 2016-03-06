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
import os
import platform
import sys

extra_install_args = ""
if len(sys.argv) == 2 and sys.argv[1].startswith("-pkg="):
  extra_install_args = " " + sys.argv[1]

print("Installing C++ library...")
os.chdir('corelib')
if platform.system() == "Windows":
    os.system('qmake -spec win32-msvc2010 "CONFIG+=release"')
    os.system('nmake')
else:
    os.system('qmake')
    os.system('make')
os.system('python install.py' + extra_install_args)

print("Installing plugin...")
os.chdir('../plugin')
os.system('python install.py' + extra_install_args)
