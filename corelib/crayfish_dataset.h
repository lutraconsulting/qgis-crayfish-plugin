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

#ifndef CRAYFISH_DATASET_H
#define CRAYFISH_DATASET_H

#include "crayfish_colormap.h"

#include <QMap>
#include <QVariant>
#include <QDateTime>

class Mesh;
class Output;
class NodeOutput;
class ElementOutput;

/**
 * DataSet represents one sub-layer of the plugin layer.
 * One mesh may have several DataSet instances attached.
 */
class DataSet
{
public:
    DataSet(const QString& fileName, size_t mIndex=0);
    ~DataSet();

    static QString sanitizeName(const QString& name);

    //! mesh to which this dataset is associated
    const Mesh* mesh() const { return mMesh; }
    void setMesh(const Mesh* m) { mMesh = m; }

    QString fileName() const { return mFileName; }

    void setName(const QString& name, bool sanitize = true);
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
    void removeOutput(Output* output);
    void removeAllOutputs();

    const Output* constOutput(int outputTime) const;
    const NodeOutput* constNodeOutput(int outputTime) const;
    const ElementOutput* constElemOutput(int outputTime) const;

    Output* output(int outputTime);
    NodeOutput* nodeOutput(int outputTime);
    ElementOutput* elemOutput(int outputTime);

    void updateZRange(int iOutput);
    void updateZRange();

    float minZValue() const { return mZMin; }
    float maxZValue() const { return mZMax; }

    void setIsTimeVarying(bool varying) { mTimeVarying = varying; }
    bool isTimeVarying() const { return mTimeVarying; }

    size_t getIndex() const {return mIndex;}

    void setRefTime(const QDateTime& dt) {refTime = dt;}
    QDateTime getRefTime() const {return refTime;}

protected:
    const Mesh* mMesh;
    QString mFileName;
    Type mType;
    QString mName;
    QVector<Output*> outputs;
    QDateTime refTime; //!< reference (base) time for output's times
    float mZMin;   //!< min Z value of data
    float mZMax;   //!< max Z value of data
    bool mTimeVarying;  //!< whether the data are time-varying (may contain more than one Output)
    size_t mIndex; //! index in the mesh Datasets array
};

#endif // CRAYFISH_DATASET_H
