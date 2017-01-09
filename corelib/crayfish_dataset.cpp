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

#include "crayfish_dataset.h"

#include "crayfish_output.h"

#include <limits>


DataSet::DataSet(const QString& fileName, size_t index)
  : mMesh(0)
  , mFileName(fileName) 
  , mIndex(index)
{
}


DataSet::~DataSet()
{
  qDeleteAll(outputs);
  outputs.clear();
}

QString DataSet::sanitizeName(const QString& name) {
    // remove units
    // slash cannot be in dataset name,
    // because it means subdataset, see
    // python class DataSetModel.setmMesh()
    // see #132
    QString nm(name);
    return nm.replace(QRegExp("\\[.+\\/.+\\]"), "").replace("/", "");
}

void DataSet::setName(const QString& name, bool sanitize) {
    mName = sanitize ? sanitizeName(name) : name;
}

void DataSet::addOutput(Output* output)
{
  outputs.push_back(output);
  output->dataSet = this;
}


const Output* DataSet::constOutput(int outputTime) const
{
  if (outputTime < 0 || outputTime >= (int)outputs.size())
    return 0;

  return outputs.at(outputTime);
}

const NodeOutput* DataSet::constNodeOutput(int outputTime) const
{
  if (const Output* o = constOutput(outputTime))
  {
    if (o->type() == Output::TypeNode)
      return static_cast<const NodeOutput*>(o);
  }
  return 0;
}

const ElementOutput* DataSet::constElemOutput(int outputTime) const
{
  if (const Output* o = constOutput(outputTime))
  {
    if (o->type() == Output::TypeElement)
      return static_cast<const ElementOutput*>(o);
  }
  return 0;
}

Output* DataSet::output(int outputTime)
{
  if (outputTime < 0 || outputTime >= (int)outputs.size())
    return 0;

  return outputs.at(outputTime);
}

NodeOutput* DataSet::nodeOutput(int outputTime)
{
  if (Output* o = output(outputTime))
  {
    if (o->type() == Output::TypeNode)
      return static_cast<NodeOutput*>(o);
  }
  return 0;
}

ElementOutput* DataSet::elemOutput(int outputTime)
{
  if (Output* o = output(outputTime))
  {
    if (o->type() == Output::TypeElement)
      return static_cast<ElementOutput*>(o);
  }
  return 0;
}

void DataSet::updateZRange()
{
  mZMin = std::numeric_limits<float>::max();
  mZMax = std::numeric_limits<float>::min();
  for(int i = 0; i < outputCount(); i++)
  {
    if (constOutput(i)->isLoaded())
    {
      updateZRange(i);
    }
  }
}

void DataSet::updateZRange(int iOutput)
{
  float outputZMin, outputZMax;
  constOutput(iOutput)->getRange(outputZMin, outputZMax);
  mZMin = qMin(outputZMin, mZMin);
  mZMax = qMax(outputZMax, mZMax);
}
