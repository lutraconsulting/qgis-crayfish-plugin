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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *
*/

#ifndef CRAYFISHVIEWER_GLOBAL_H
#define CRAYFISHVIEWER_GLOBAL_H

#include <QtCore/qglobal.h>
#include <QString>
#include <vector>

#if defined(CRAYFISHVIEWER_LIBRARY)
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_EXPORT
#else
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_IMPORT
#endif

namespace ElementType{
    enum Enum{
        Undefined,
        E4Q,
        E3T
    };
}

namespace ViewerError{
    enum Enum{
        None,
        FileNotFound
    };
}

namespace ViewerWarning{
    enum Enum{
        None,
        UnsupportedElement,
        InvalidElements
    };
}

namespace DataSetType{
    enum Enum{
        Bed,
        Scalar,
        Vector
    };
}

struct Node{
    uint index;
    double x;
    double y;
};

struct Element{
    uint index;
    ElementType::Enum eType;
    int nodeCount;
    bool isDummy;
    Node* p1;   // Top-Right node
    Node* p2;   // Top-Left node
    Node* p3;   // Bottom-Left node
    Node* p4;   // Bottom-Right node // FIXME - this is irrelevant for a triangle but should make no harm
    double maxSize; // Largest distance (real world) across the element
    double minX;
    double maxX;
    double minY;
    double maxY;

    int indexTmp; //!< index into array with temporary information for particular element type
};

/** auxilliary cached data used for rendering of E4Q elements */
struct E4Qtmp
{
  //uint elemIndex; //!< index of the element in mElems
  double a[4], b[4]; //!< coefficients for mapping between physical and logical coords
};

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

    float time;
    char* statusFlags;   //!< array determining which elements are active and therefore if they should be rendered (size = element count)
    float* values;       //!< array of values per node (size = node count)
    float* values_x;     //!< in case of dataset with vector data - array of X coords - otherwise 0
    float* values_y;     //!< in case of dataset with vector data - array of Y coords - otherwise 0
};

enum VectorLengthMethod{
    MinMax,  //!< minimal and maximal length
    Scaled,  //!< length is scaled proportionally to the magnitude
    Fixed    //!< length is fixed to a certain value
};

/**
 * DataSet represents one sub-layer of the plugin layer.
 * One mesh may have several DataSet instances attached.
 */
struct CRAYFISHVIEWERSHARED_EXPORT DataSet
{
    DataSet(const QString& fileName)
      : mFileName(fileName)
      , mCurrentOutputTime(0)
      , mRenderContours(true)
      , mContouredAutomatically(true)
      , mContourMin(0)
      , mContourMax(0)
      , mContourAlpha(255)
      , mRenderVectors(false)
    {
    }

    ~DataSet()
    {
      for (size_t j=0; j<outputs.size(); j++)
          delete outputs.at(j);
      outputs.clear();
    }

    QString fileName() const { return mFileName; }

    void setName(const QString& name) { mName = name; }
    QString name() const { return mName; }

    void setType(DataSetType::Enum t) { mType = t; }
    DataSetType::Enum type() const { return mType; }

    uint outputCount() const { return outputs.size(); }

    void addOutput(Output* output) { outputs.push_back(output); }

    void setCurrentOutputTime(int outputTime)
    {
      // If we're looking at bed elevation, ensure the time output is the first (and only)
      if (mType == DataSetType::Bed)
          outputTime = 0;

      mCurrentOutputTime = outputTime;
    }
    int currentOutputTime() const { return mCurrentOutputTime; }
    const Output* output(int outputTime) const
    {
      if (outputTime < 0 || outputTime >= (int)outputs.size())
        return 0;

      return outputs.at(outputTime);
    }
    const Output* currentOutput() const
    {
      return output(mCurrentOutputTime);
    }

    void updateZRange(uint nodeCount)
    {
      bool first = true;
      float zMin = 0.0;
      float zMax = 0.0;
      for(uint i=0; i<outputCount(); i++){
          const Output* out = output(i);
          for(uint j=0; j<nodeCount; j++){
              if(out->values[j] != -9999.0){
                  // This is not a NULL value
                  if(first){
                      first = false;
                      zMin = out->values[j];
                      zMax = out->values[j];
                  }
                  if( out->values[j] < zMin ){
                      zMin = out->values[j];
                  }
                  if( out->values[j] > zMax ){
                      zMax = out->values[j];
                  }
              }
          }
      }

      mZMin = zMin;
      mZMax = zMax;
    }

    float minZValue() const { return mZMin; }
    float maxZValue() const { return mZMax; }

    void setIsTimeVarying(bool varying) { mTimeVarying = varying; }
    bool isTimeVarying() const { return mTimeVarying; }

    // -- contour rendering --

    void setContourRenderingEnabled(bool enabled) { mRenderContours = enabled; }
    bool isContourRenderingEnabled() const { return mRenderContours; }

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

#endif // CRAYFISHVIEWER_GLOBAL_H
