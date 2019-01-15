# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2019 Lutra Consulting Limited

# info at lutraconsulting dot co dot uk
# Lutra Consulting Limited
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

import math


def integrate(x, y):
    """
    Calculate approximate value of integral for x,y arrays.
    Arrays containing NaN values will be split into parts.

    :param x: list of x points
    :param y: list of f(x) points
    :return: value of integration
    """
    if len(x) != len(y):
        return
    # calculate parts where f(x) is not NaN
    parts = []
    _x, _y = [], []
    for index, i in enumerate(y):
        if not math.isnan(i) and not math.isnan(x[index]):
            _x.append(x[index])
            _y.append(y[index])
        else:
            parts.append([_x, _y])
            _x, _y = [], []
    parts.append([_x, _y])

    # approximated integral(a,b) f(x) as (b-a)/N sum(0,N) f(x_n)
    integral = 0
    for part in parts:
        if len(part[1]):
            integral += sum(part[1]) * (part[0][-1]-part[0][0]) / len(part[1])
    return integral
