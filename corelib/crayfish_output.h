/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2016 Lutra Consulting

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

#include <QVector>

#include <math.h>
#include <limits>

class DataSet;

//! Base class for results for one particular quantity in one timestep
class Output
{
public:
  Output()
    : dataSet(0)
    , time(-1)
  {
  }

  virtual ~Output()
  {
  }

  enum Type
  {
    TypeNode,      //!< node (mesh) centered results
    TypeElement,   //!< element centered results
  };

  virtual Type type() const = 0;

  //! find out the minimum and maximum from all values
  virtual void getRange(float& zMin, float& zMax) const = 0;

  //! find out whether an element is active in this output
  virtual bool isActive(int elemIndex) const { Q_UNUSED(elemIndex); return true; }

  typedef struct
  {
    float x,y;
    float length() const { return sqrt( x*x + y*y ); }
  } float2D;


  const DataSet* dataSet;  //!< dataset to which this data belong
  float time;               //!< time since beginning of simulation (in hours)
};


//! Results stored in nodes of the mesh
class NodeOutput : public Output
{
public:

  virtual Type type() const { return TypeNode; }

  virtual void getRange(float& zMin, float& zMax) const
  {
    zMin = std::numeric_limits<float>::max();
    zMax = std::numeric_limits<float>::min();
    const float* v = values.constData();
    for (int j = 0; j < values.count(); ++j)
    {
      if (v[j] != -9999.0)
      {
        // This is not a NULL value
        if( v[j] < zMin )
            zMin = v[j];
        if( v[j] > zMax )
            zMax = v[j];
      }
    }
  }

  virtual bool isActive(int elemIndex) const { return active[elemIndex]; }

  void init(int nodeCount, int elemCount, bool isVector)
  {
    active.resize(elemCount);
    values.resize(nodeCount);
    if (isVector)
    {
      valuesV.resize(nodeCount);
    }
  }

  QVector<char> active;     //!< array determining which elements are active and therefore if they should be rendered (size = element count)
  QVector<float> values;    //!< array of values per node (size = node count)
  QVector<float2D> valuesV; //!< in case of dataset with vector data - array of X,Y coords - otherwise empty
};


//! Element-centered results
class ElementOutput : public Output
{
public:
  // TODO

  virtual Type type() const { return TypeElement; }

  virtual void getRange(float& zMin, float& zMax) const
  {
    zMin = std::numeric_limits<float>::max();
    zMax = std::numeric_limits<float>::min();
    const float* v = values.constData();
    for (int j = 0; j < values.count(); ++j)
    {
      if (!isActive(j))
        continue;

      if (v[j] != -9999.0)
      {
        // This is not a NULL value
        if( v[j] < zMin )
            zMin = v[j];
        if( v[j] > zMax )
            zMax = v[j];
      }
    }
  }

  void init(int elemCount, bool isVector)
  {
    values.resize(elemCount);
    if (isVector)
      valuesV.resize(elemCount);
  }

  virtual bool isActive(int elemIndex) const { return values[elemIndex] != -9999.0; }

  QVector<float> values;    //!< array of values per element (size = element count)
  QVector<float2D> valuesV; //!< in case of dataset with vector data - array of X,Y coords - otherwise empty
};

#endif // CRAYFISH_OUTPUT_H
