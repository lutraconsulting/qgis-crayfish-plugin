/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2012 Peter Wells for Lutra Consulting

peter dot wells at lutraconsulting dot co dot uk
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

#include "crayfish_viewer_global.h"

#include "crayfish_colormap.h"

struct Output;

/**
 * DataSet represents one sub-layer of the plugin layer.
 * One mesh may have several DataSet instances attached.
 */
struct CRAYFISHVIEWERSHARED_EXPORT DataSet
{
    DataSet(const QString& fileName);
    ~DataSet();

    QString fileName() const { return mFileName; }

    void setName(const QString& name) { mName = name; }
    QString name() const { return mName; }

    void setType(DataSetType::Enum t) { mType = t; }
    DataSetType::Enum type() const { return mType; }

    uint outputCount() const { return outputs.size(); }

    void addOutput(Output* output) { outputs.push_back(output); }

    void setCurrentOutputTime(int outputTime);
    int currentOutputTime() const { return mCurrentOutputTime; }
    const Output* output(int outputTime) const;
    const Output* currentOutput() const { return output(mCurrentOutputTime); }

    void updateZRange(uint nodeCount);

    float minZValue() const { return mZMin; }
    float maxZValue() const { return mZMax; }

    void setIsTimeVarying(bool varying) { mTimeVarying = varying; }
    bool isTimeVarying() const { return mTimeVarying; }

    // -- contour rendering --

    void setContourRenderingEnabled(bool enabled) { mRenderContours = enabled; }
    bool isContourRenderingEnabled() const { return mRenderContours; }

    void setContourColorMap(const ColorMap& cm) { mColorMap = cm; }
    const ColorMap& contourColorMap() const { return mColorMap; }

    void setContourAutoRange(bool enabled) { mContouredAutomatically = enabled; }
    bool contourAutoRange() const { return mContouredAutomatically; }

    void setContourCustomRange(float vMin, float vMax) { mContourMin = vMin; mContourMax = vMax; }
    float contourCustomRangeMin() const { return mContourMin; }
    float contourCustomRangeMax() const { return mContourMax; }

    void setContourAlpha(int alpha) { mContourAlpha = alpha; }
    int contourAlpha() const { return mContourAlpha; }

    // -- vector rendering --

    void setVectorRenderingEnabled(bool enabled) { mRenderVectors = enabled; }
    bool isVectorRenderingEnabled() const { return mRenderVectors; }

    void setVectorShaftLengthMethod(VectorLengthMethod method) { mShaftLengthMethod = method; }
    VectorLengthMethod vectorShaftLengthMethod() const { return mShaftLengthMethod; }

    void setVectorShaftLengthMinMax(float minLen, float maxLen) { mMinShaftLength = minLen; mMaxShaftLength = maxLen; }
    float vectorShaftLengthMin() const { return mMinShaftLength; }
    float vectorShaftLengthMax() const { return mMaxShaftLength; }

    void setVectorShaftLengthScaleFactor(float scaleFactor) { mScaleFactor = scaleFactor; }
    float vectorShaftLengthScaleFactor() const { return mScaleFactor; }

    void setVectorShaftLengthFixed(float fixedLen) { mFixedShaftLength = fixedLen; }
    float vectorShaftLengthFixed() const { return mFixedShaftLength; }

    void setVectorPenWidth(int width) { mLineWidth = width; }
    int vectorPenWidth() const { return mLineWidth; }

    void setVectorHeadSize(float widthPerc, float lengthPerc) { mVectorHeadWidthPerc = widthPerc; mVectorHeadLengthPerc = lengthPerc; }
    float vectorHeadWidth() const { return mVectorHeadWidthPerc; }
    float vectorHeadLength() const { return mVectorHeadLengthPerc; }

protected:

    QString mFileName;
    DataSetType::Enum mType;
    QString mName;
    std::vector<Output*> outputs;
    float mZMin;   //!< min Z value of data
    float mZMax;   //!< max Z value of data
    bool mTimeVarying;  //!< whether the data are time-varying (may contain more than one Output)

    int mCurrentOutputTime; //!< current time index for rendering

    // contour rendering settings
    bool mRenderContours; //!< whether to render contours
    bool mContouredAutomatically;  //!< whether the min/max Z value should be used from full data range
    float mContourMin;  //!< min Z value for rendering of contours
    float mContourMax;  //!< max Z value for rendering of contours
    int mContourAlpha;  //!< alpha value (opaqueness) of contours (0 = transparent, 255 = opaque)
    ColorMap mColorMap; //!< actual color map used for rendering

    // vector rendering settings
    bool mRenderVectors;  //!< whether to render vectors (only valid for vector data)
    VectorLengthMethod mShaftLengthMethod;
    float mMinShaftLength;    //!< valid if using "min/max" method
    float mMaxShaftLength;    //!< valid if using "min/max" method
    float mScaleFactor;       //!< valid if using "scaled" method
    float mFixedShaftLength;  //!< valid if using "fixed" method
    int mLineWidth;           //!< pen width for drawing of the vectors
    float mVectorHeadWidthPerc;   //!< arrow head's width  (in percent to shaft's length)
    float mVectorHeadLengthPerc;  //!< arrow head's length (in percent to shaft's length)
};


#endif // CRAYFISH_DATASET_H
