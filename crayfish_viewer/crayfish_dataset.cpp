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

#include "crayfish_dataset.h"

#include "crayfish_output.h"



DataSet::DataSet(const QString& fileName)
  : mMesh(0)
  , mFileName(fileName)
  , mCurrentOutputTime(0)
  , mRenderContours(true)
  , mRenderVectors(false)
  , mShaftLengthMethod(MinMax)
  , mMinShaftLength(3)
  , mMaxShaftLength(40)
  , mScaleFactor(10)
  , mFixedShaftLength(10)
  , mLineWidth(1)
  , mVectorHeadWidthPerc(15)
  , mVectorHeadLengthPerc(40)
{
}


DataSet::~DataSet()
{
  for (size_t j=0; j<outputs.size(); j++)
      delete outputs.at(j);
  outputs.clear();
}

void DataSet::addOutput(Output* output)
{
  outputs.push_back(output);
  output->dataSet = this;
}


void DataSet::setCurrentOutputTime(int outputTime)
{
  // If we're looking at bed elevation, ensure the time output is the first (and only)
  if (mType == DataSet::Bed)
      outputTime = 0;

  mCurrentOutputTime = outputTime;
}


const Output* DataSet::output(int outputTime) const
{
  if (outputTime < 0 || outputTime >= (int)outputs.size())
    return 0;

  return outputs.at(outputTime);
}


void DataSet::updateZRange(uint nodeCount)
{
  bool first = true;
  float zMin = 0.0;
  float zMax = 0.0;
  for(uint i=0; i<outputCount(); i++){
      const Output* out = output(i);
      const float* values = out->values.constData();
      for(uint j=0; j<nodeCount; j++){
          if(values[j] != -9999.0){
              // This is not a NULL value
              if(first){
                  first = false;
                  zMin = values[j];
                  zMax = values[j];
              }
              if( values[j] < zMin ){
                  zMin = values[j];
              }
              if( values[j] > zMax ){
                  zMax = values[j];
              }
          }
      }
  }

  mZMin = zMin;
  mZMax = zMax;

  mColorMap = ColorMap::defaultColorMap(mZMin, mZMax);
}

