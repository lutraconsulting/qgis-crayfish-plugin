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
struct Output;

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

    uint outputCount() const { return outputs.size(); }

    void addOutput(Output* output);

    void setCurrentOutputTime(int outputTime);
    int currentOutputTime() const { return mCurrentOutputTime; }
    const Output* output(int outputTime) const;
    const Output* currentOutput() const { return output(mCurrentOutputTime); }

    void updateZRange(uint nodeCount);

    float minZValue() const { return mZMin; }
    float maxZValue() const { return mZMax; }

    void setIsTimeVarying(bool varying) { mTimeVarying = varying; }
    bool isTimeVarying() const { return mTimeVarying; }



    //const RendererConfig& config() const { return mCfg; }

    // -- contour rendering --
/*
    void setContourRenderingEnabled(bool enabled) { mCfg.mRenderContours = enabled; }
    bool isContourRenderingEnabled() const { return mCfg.mRenderContours; }

    void setContourColorMap(const ColorMap& cm) { mCfg.mColorMap = cm; }
    const ColorMap& contourColorMap() const { return mCfg.mColorMap; }

    // -- vector rendering --

    void setVectorRenderingEnabled(bool enabled) { mCfg.mRenderVectors = enabled; }
    bool isVectorRenderingEnabled() const { return mCfg.mRenderVectors; }

    void setVectorShaftLengthMethod(VectorLengthMethod method) { mCfg.mShaftLengthMethod = method; }
    VectorLengthMethod vectorShaftLengthMethod() const { return mCfg.mShaftLengthMethod; }

    void setVectorShaftLengthMinMax(float minLen, float maxLen) { mCfg.mMinShaftLength = minLen; mCfg.mMaxShaftLength = maxLen; }
    float vectorShaftLengthMin() const { return mCfg.mMinShaftLength; }
    float vectorShaftLengthMax() const { return mCfg.mMaxShaftLength; }

    void setVectorShaftLengthScaleFactor(float scaleFactor) { mCfg.mScaleFactor = scaleFactor; }
    float vectorShaftLengthScaleFactor() const { return mCfg.mScaleFactor; }

    void setVectorShaftLengthFixed(float fixedLen) { mCfg.mFixedShaftLength = fixedLen; }
    float vectorShaftLengthFixed() const { return mCfg.mFixedShaftLength; }

    void setVectorPenWidth(int width) { mCfg.mLineWidth = width; }
    int vectorPenWidth() const { return mCfg.mLineWidth; }

    void setVectorHeadSize(float widthPerc, float lengthPerc) { mCfg.mVectorHeadWidthPerc = widthPerc; mCfg.mVectorHeadLengthPerc = lengthPerc; }
    float vectorHeadWidth() const { return mCfg.mVectorHeadWidthPerc; }
    float vectorHeadLength() const { return mCfg.mVectorHeadLengthPerc; }
*/
    // -- custom (GUI-specific) settings --

    void setCustomValue(const QString& key, const QVariant& value) { mCustomSettings.insert(key, value); }
    QVariant customValue(const QString& key) const { return mCustomSettings.value(key); }
    void clearCustomValue(const QString& key) { mCustomSettings.remove(key); }
    QStringList customValues() const { return mCustomSettings.keys(); }



protected:

    const Mesh* mMesh;
    QString mFileName;
    Type mType;
    QString mName;
    std::vector<Output*> outputs;
    float mZMin;   //!< min Z value of data
    float mZMax;   //!< max Z value of data
    bool mTimeVarying;  //!< whether the data are time-varying (may contain more than one Output)

    int mCurrentOutputTime; //!< current time index for rendering

    QMap<QString, QVariant> mCustomSettings;
};

#endif // CRAYFISH_DATASET_H
