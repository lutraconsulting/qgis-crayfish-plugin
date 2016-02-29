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

#ifndef CRAYFISH_DATASET_H
#define CRAYFISH_DATASET_H

#include "crayfish_colormap.h"

#include <QMap>
#include <QVariant>

class Mesh;
class Output;
class NodeOutput;
class ElementOutput;

/**
 * DataSet represents one sub-layer of the plugin layer.
 * One mesh may have several DataSet instances attached.
 */
struct DataSet
{
    DataSet(const QString& fileName);
    ~DataSet();

    //! mesh to which this dataset is associated
    const Mesh* mesh() const { return mMesh; }
    void setMesh(const Mesh* m) { mMesh = m; }

    QString fileName() const { return mFileName; }

    void setName(const QString& name) { mName = name; }
    QString name() const { return mName; }

    enum Type
    {
      Bed,
      Scalar,
      Vector
    };

    void setType(Type t) { mType = t; }
    Type type() const { return mType; }

    int outputCount() const { return outputs.size(); }

    void addOutput(Output* output);

    const Output* output(int outputTime) const;

    const NodeOutput* nodeOutput(int outputTime) const;

    void updateZRange();

    float minZValue() const { return mZMin; }
    float maxZValue() const { return mZMax; }

    void setIsTimeVarying(bool varying) { mTimeVarying = varying; }
    bool isTimeVarying() const { return mTimeVarying; }


protected:

    const Mesh* mMesh;
    QString mFileName;
    Type mType;
    QString mName;
    QVector<Output*> outputs;
    float mZMin;   //!< min Z value of data
    float mZMax;   //!< max Z value of data
    bool mTimeVarying;  //!< whether the data are time-varying (may contain more than one Output)

};

#endif // CRAYFISH_DATASET_H
