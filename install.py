#!/usr/bin/env python
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

from __future__ import print_function
import os
import platform
import sys

def run_cmd(cmd, err_msg=None):
    res = os.system(cmd)
    if res != 0:
        if not err_msg:
            err_msg = "\"{}\" command failed".format(cmd)
        raise Exception(err_msg)

def make_and_install(extra_install_args):
    print("Installing C++ library...")
    os.chdir('corelib')
    if platform.system() == "Windows":
        run_cmd('qmake -spec win32-msvc2010 "CONFIG+=release"')
        run_cmd('nmake')
    elif platform.system() == "Linux":
        try:
	    if run_cmd('qmake -v | grep -o " 4." | wc -l'):
	        run_cmd('qmake')
	    else:	
            	# Run explicitly suffixed -qt4.
                run_cmd('qmake-qt4')
        except Exception:
            run_cmd('qmake')

        run_cmd('make')
    else: #OSX
        run_cmd('qmake -spec macx-g++ "CONFIG+=release"')
        run_cmd('make')

    run_cmd('python install.py' + extra_install_args, err_msg="install of core library failed!")

    print("Installing plugin...")
    os.chdir(os.path.join(os.pardir, 'crayfish'))
    run_cmd('python install.py' + extra_install_args, err_msg="install of python plugin failed!")

if __name__ == "__main__":
    extra_install_args = ""
    if len(sys.argv) == 2 and sys.argv[1].startswith("-pkg="):
        extra_install_args = " " + sys.argv[1]
    make_and_install(extra_install_args)
