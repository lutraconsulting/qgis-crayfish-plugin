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

#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_renderer.h"
//struct Element;
struct Node;
struct BBox;
struct E4Qtmp;

struct DataSet;
struct Output;
class MapToPixel;







class CrayfishViewer {
public:

    CrayfishViewer(QString);
    ~CrayfishViewer();
    QImage draw(const QSize& outputSize, double llX, double llY, double pixelSize);

    bool loadedOk(){ return mLoadStatus.mLastError == LoadStatus::Err_None; }
    bool warningsEncountered(){ return mLoadStatus.mLastWarning != LoadStatus::Warn_None; }
    LoadStatus::Warning getLastWarning(){ return mLoadStatus.mLastWarning; }
    LoadStatus::Error getLastError() { return mLoadStatus.mLastError; }
    bool loadDataSet(QString fileName);
    bool isDataSetLoaded(QString fileName);

    // mesh information

    int nodeCount() const { return mMesh->nodes().count(); }
    const Node* nodes() const { return mMesh->nodes().data(); }
    int elementCount() const { return mMesh->elements().count(); }
    const Element* elements() const { return mMesh->elements().data(); }
    int elementCount_E4Q() const { return mMesh ? mMesh->elementCountForType(Element::E4Q) : 0; }
    int elementCount_E3T() const { return mMesh ? mMesh->elementCountForType(Element::E3T) : 0; }
    //QRectF meshExtent() const { return QRectF(QPointF(mXMin,mYMin), QPointF(mXMax,mYMax)); }

    // rendering options

    void setCanvasSize(const QSize& size);
    QSize canvasSize() const;

    void setExtent(double llX, double llY, double pixelSize);
    QRectF extent() const;
    double pixelSize() const;

    void setMeshRenderingEnabled(bool enabled);
    bool isMeshRenderingEnabled() const;

    void setMeshColor(const QColor& color);
    QColor meshColor() const;

    void setCurrentDataSetIndex(int index);
    int currentDataSetIndex() const;
    int dataSetCount() const { return mMesh->dataSets().count(); }
    const DataSet* dataSet(int dataSetIndex) const;
    const DataSet* currentDataSet() const;

private:

    //! mesh topology and associated data
    Mesh* mMesh;

    // global rendering options
    Renderer::Config::Mesh mCfgMesh;
    int mCurDataSetIdx; //!< index of the current dataset

    LoadStatus mLoadStatus; // TODO: remove

};


#endif // CRAYFISHVIEWER_H
