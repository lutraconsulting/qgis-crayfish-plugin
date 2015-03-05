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

#include <QVector>

#include <math.h>

class DataSet;

struct CRAYFISHVIEWERSHARED_EXPORT Output{

    Output()
      : dataSet(0)
      , time(-1)
    {
    }

    ~Output()
    {
    }

    void init(int nodeCount, int elemCount, bool isVector)
    {
      active.resize(elemCount);
      values.resize(nodeCount);
      if (isVector)
      {
        valuesV.resize(nodeCount);
      }
    }

    typedef struct
    {
      float x,y;
      float length() const { return sqrt( x*x + y*y ); }
    } float2D;

    const DataSet* dataSet;  //!< dataset to which this data belong

    float time;               //!< time since beginning of simulation (in hours)
    QVector<char> active;     //!< array determining which elements are active and therefore if they should be rendered (size = element count)
    QVector<float> values;    //!< array of values per node (size = node count)
    QVector<float2D> valuesV; //!< in case of dataset with vector data - array of X,Y coords - otherwise empty
};

#endif // CRAYFISH_OUTPUT_H
