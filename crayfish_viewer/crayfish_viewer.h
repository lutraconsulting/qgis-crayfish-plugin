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

#ifndef CRAYFISHVIEWER_H
#define CRAYFISHVIEWER_H

#include "crayfish_viewer_global.h"

#include <QImage>
#include <QPainter>
#include <QFile>
#include <QTextStream>
#include <QStringList>
#include <QColor>

#include <math.h>

class CRAYFISHVIEWERSHARED_EXPORT CrayfishViewer {
public:
    enum VectorLengthMethod{
        DefineMinAndMax,
        Scaled,
        Fixed
    };
    CrayfishViewer(QString);
    ~CrayfishViewer();
    QImage* draw(bool,
                 bool,
                 int,
                 int,
                 double,
                 double,
                 double,
                 int dataSetIdx,
                 int outputTime,

                 bool autoContour,
                 float minContour,
                 float maxContour,

                 VectorLengthMethod shaftLengthCalculationMethod,
                 float minShaftLength,
                 float maxShaftLength,
                 float scaleFactor,
                 float fixedShaftLength,
                 int lineWidth, float vectorHeadWidthPerc, float vectorHeadLengthPerc);

    bool loadedOk(){ return mLoadedSuccessfully; }
    bool warningsEncountered(){ return mWarningsEncountered; }
    int getLastWarning(){ return mLastWarning; }
    QRectF getExtents(){ return QRectF(QPointF(mXMin,mYMax), QPointF(mXMax,mYMin)); }
    bool loadDataSet(QString);
    int dataSetCount(){ return mDataSets.size(); }
    QString* dataSetName(int dataSet){ return &mDataSets.at(dataSet)->name; }
    int dataSetOutputCount(int dataSet){ return mDataSets.at(dataSet)->outputs.size(); }
    float dataSetOutputTime(int dataSet, int output){ return mDataSets.at(dataSet)->outputs.at(output)->time; }
    bool timeVarying(int dataSet){ return mDataSets.at(dataSet)->timeVarying; }
    int getLastRenderIndex(int dataSet){ return mDataSets.at(dataSet)->lastOutputRendered; }
    bool layerContouredAutomatically(int dataSet){ return mDataSets.at(dataSet)->contouredAutomatically; }
    float minValue(int dataSet){ return mDataSets.at(dataSet)->mZMin; }
    float maxValue(int dataSet){ return mDataSets.at(dataSet)->mZMax; }
    float lastMinContourValue(int dataSet);
    float lastMaxContourValue(int dataSet);
    bool isBed(int dataSet){ return mDataSets.at(dataSet)->isBed; }
    bool isVector(int dataSet){ return (mDataSets.at(dataSet)->type == DataSetType::Vector); }
    bool displayContours(int dataSet){ return mDataSets.at(dataSet)->renderContours; }
    bool displayVectors(int dataSet){ return mDataSets.at(dataSet)->renderVectors; }
    bool displayMesh() { return mRenderMesh; }
    void setDisplayMesh(bool display) { mRenderMesh = display; }
    double valueAtCoord(int dataSetIdx, int timeIndex, double xCoord, double yCoord);
private:
    bool mLoadedSuccessfully;
    bool mWarningsEncountered;
    ViewerError::Enum mLastError;
    ViewerWarning::Enum mLastWarning;
    QImage* mImage;
    int mCanvasWidth;
    int mCanvasHeight;
    double mLlX;
    double mLlY;
    double mUrX;
    double mUrY;
    double mPixelSize;
    double mXMin;
    double mXMax;
    double mYMin;
    double mYMax;
    uint mElemCount;
    Element* mElems;
    uint mNodeCount;
    uint mRotatedNodeCount;
    Node* mNodes;
    Node* mRotatedNodes;
    std::vector<DataSet*> mDataSets;
    bool mRenderMesh;

    bool elemOutsideView(uint);
    QPoint realToPixel(double, double);
    QPointF realToPixelF(double, double);
    void paintRow(uint, int, int, int, int dataSetIdx, int outputTime);
    bool interpolatValue(uint, double, double, double*, int dataSetIdx, int outputTime);
    QPointF pixelToReal(int, int);
    void setColorFromVal(double, QColor *col, int dataSetIdx);
};

float absolute(float input){
    if(input < 0.0){
        input *= -1.0;
    }
    return input;
}

float mag(float input){
    if(input < 0.0){
        return -1.0;
    }
    return 1.0;
}

#endif // CRAYFISHVIEWER_H
