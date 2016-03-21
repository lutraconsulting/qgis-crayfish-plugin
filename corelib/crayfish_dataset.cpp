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

#include <limits>


DataSet::DataSet(const QString& fileName)
  : mMesh(0)
  , mFileName(fileName)
{
}


DataSet::~DataSet()
{
  qDeleteAll(outputs);
  outputs.clear();
}

void DataSet::setName(const QString& name) {
    // remove units
    // slash cannot be in dataset name,
    // because it means subdataset, see
    // python class DataSetModel.setmMesh()
    // see #132
    mName = name;
    mName = mName.replace(QRegExp("\\[.+\\/.+\\]"), "").replace("/", "");
}

void DataSet::addOutput(Output* output)
{
  outputs.push_back(output);
  output->dataSet = this;
}


const Output* DataSet::output(int outputTime) const
{
  if (outputTime < 0 || outputTime >= (int)outputs.size())
    return 0;

  return outputs.at(outputTime);
}

const NodeOutput* DataSet::nodeOutput(int outputTime) const
{
  if (const Output* o = output(outputTime))
  {
    if (o->type() == Output::TypeNode)
      return static_cast<const NodeOutput*>(o);
  }
  return 0;
}

void DataSet::updateZRange()
{
  mZMin = std::numeric_limits<float>::max();
  mZMax = std::numeric_limits<float>::min();
  for(int i = 0; i < outputCount(); i++)
  {
    float outputZMin, outputZMax;
    output(i)->getRange(outputZMin, outputZMax);
    mZMin = qMin(outputZMin, mZMin);
    mZMax = qMax(outputZMax, mZMax);
  }
}

