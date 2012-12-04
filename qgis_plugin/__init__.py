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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *

def name():
    return "Crayfish"
def description():
    return "A collection of tools for TUFLOW and other hydraulic modelling packages"
def version():
    return "Version 1.0.1"
def qgisMinimumVersion():
    return "1.7"
def authorName():
    return "Peter Wells for Lutra Consulting"
def author():
    return "Peter Wells for Lutra Consulting"
def email():
    return "peter.wells@lutraconsulting.co.uk"
def homepage():
    return "http://www.lutraconsulting.co.uk/resources/crayfish"
def classFactory(iface):
    from crayfish_plugin import CrayfishPlugin
    return CrayfishPlugin(iface)
