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

from math import *

def interpolate( points, x, y ):
    
    x1 = points[2]['x']
    y1 = points[2]['y']
    q11 = points[2]['z']

    _x1 = points[1]['x']
    y2 = points[1]['y']
    q12 = points[1]['z']

    x2 = points[3]['x']
    _y1 = points[3]['y']
    q21 = points[3]['z']

    _x2 = points[0]['x']
    _y2 = points[0]['y']
    q22 = points[0]['z']
    
    return (q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1) ) / ( (x2 - x1) * (y2 - y1) + 0.0 )
                
def rotate(points, angle):
    for p in points:
        oldX = p['x']
        oldY = p['y']
        p['x'] = (oldX * cos(angle / (2 * pi))) - (oldY * sin(angle / (2 * pi)))
        p['y'] = (oldX * sin(angle / (2 * pi))) + (oldY * cos(angle / (2 * pi)))
        
    return points


points = []
p = { 'x' : 10.0, 'y' : 10.0, 'z' : 0.0 }
points.append(p)
p = { 'x' : 0.0, 'y' : 10.0, 'z' : 40.0 }
points.append(p)
p = { 'x' : 0.0, 'y' : 0.0, 'z' : 10.0 }
points.append(p)
p = { 'x' : 10.0, 'y' : 0.0, 'z' : 20.0 }
points.append(p)

print 'Standard: ' + str( interpolate(points, 3.2, 6.5) )

rot = -40.0
while rot <= 40.0:
    points = rotate(points, rot)
    print 'Rot ' + str(rot) + ' : ' + str( interpolate(points, 3.2, 6.5) )
    rot += 3.0

