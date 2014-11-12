/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2014 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#ifndef CRAYFISH_OUTPUT_H
#define CRAYFISH_OUTPUT_H

#include "crayfish_viewer_global.h"

struct CRAYFISHVIEWERSHARED_EXPORT Output{

    Output()
      : statusFlags(0)
      , values(0)
      , values_x(0)
      , values_y(0)
    {
    }

    ~Output()
    {
      delete[] statusFlags;
      delete[] values;
      delete[] values_x;
      delete[] values_y;
    }

    void init(int nodeCount, int elemCount, bool isVector)
    {
      Q_ASSERT(statusFlags == 0 && values == 0 && values_x == 0 && values_y == 0);
      statusFlags = new char[elemCount];
      values = new float[nodeCount];
      if (isVector)
      {
        values_x = new float[nodeCount];
        values_y = new float[nodeCount];
      }
    }

    float time;          //!< time since beginning of simulation (in hours)
    char* statusFlags;   //!< array determining which elements are active and therefore if they should be rendered (size = element count)
    float* values;       //!< array of values per node (size = node count)
    float* values_x;     //!< in case of dataset with vector data - array of X coords - otherwise 0
    float* values_y;     //!< in case of dataset with vector data - array of Y coords - otherwise 0
};

#endif // CRAYFISH_OUTPUT_H
