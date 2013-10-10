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

import os
import sys
import sipconfig
from PyQt4 import pyqtconfig

sip_file = "crayfish_viewer.sip"       # input SIP file
build_debug = False                    # whether to use debug version of the C++ library
build_cpp_basedir = "build"            # build directory with C++ library (in debug/release subdir)
build_cpp_lib = "crayfishViewer"       # name of the C++ library
build_basedir = "build-python"         # python module's base build directory
build_file = "crayfish_viewer.sbf"     # file that will be generated and used by SIP

if len(sys.argv) == 2:
  if sys.argv[1] == '-debug':
    build_debug = True
  else:
    print "build-python.py [-debug]"
    print ""
    print "  Script for building Crayfish python module with SIP"
    print ""
    print "  Arguments:"
    print "  -debug    Build debug version of Crayfish C++ library"
    sys.exit(0)

build_dir = os.path.join(build_basedir, "debug" if build_debug else "release")
build_cpp_dir = os.path.join("..","..", build_cpp_basedir, "debug" if build_debug else "release")

# Get into the build directory
if not os.path.exists(build_dir):
  os.makedirs(build_dir)
print "cd "+build_dir
os.chdir(build_dir)


# Get the PyQt configuration information.
config = pyqtconfig.Configuration()

# Prepare SIP command line
# Note that we tell SIP where to find the qt module's specification files using the -I flag.
sip_cmd = " ".join([config.sip_bin, "-c", ".", "-b", build_file, "-I", config.pyqt_sip_dir, config.pyqt_sip_flags, os.path.join("..","..",sip_file)])

# Run SIP to generate the code.
print sip_cmd
errcode = os.system(sip_cmd)
if errcode != 0:
  print "=== SIP failed ==="
  sys.exit(1)

# Create the Makefile.  The QtGuiModuleMakefile class provided by the
# pyqtconfig module takes care of all the extra preprocessor, compiler and
# linker flags needed by the Qt library.
makefile = pyqtconfig.QtGuiModuleMakefile(
    configuration=config,
    build_file=build_file
)

makefile.extra_include_dirs = [os.path.join("..","..")]  # this directory is grandparent to the actual build dir

# Add the library we are wrapping.  The name doesn't include any platform
# specific prefixes or extensions (e.g. the "lib" prefix on UNIX, or the
# ".dll" extension on Windows).
if sys.platform != 'win32':
    # Linux
    makefile.extra_lib_dirs = [build_cpp_dir]
    makefile.extra_libs = [build_cpp_lib]

    # set RPATH to $ORIGIN - that is, use module's directory to find libs
    # (no need to setup LD_LIBRARY_PATH for the c++ crayfishviewer shared lib)
    # The double dollar symbol and quotes are necessary because of make's and shell's evaluation of variables
    makefile.extra_lflags = ["-Wl,-rpath='$$ORIGIN'"]
else:
    # Windows
    makefile.extra_libs = [os.path.join(build_cpp_dir, build_cpp_lib)]

# Generate the Makefile itself.
makefile.generate()

# Run make
res = os.system('make')
if res != 0:
  print "=== make failed ==="
  sys.exit(1)
