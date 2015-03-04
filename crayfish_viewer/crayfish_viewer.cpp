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

#include "crayfish_viewer.h"

#include "crayfish_dataset.h"
#include "crayfish_e4q.h"
#include "crayfish_gdal.h"
#include "crayfish_mesh.h"
#include "crayfish_output.h"
#include "crayfish.h"

#include <iostream>

#include <QFileInfo>
#include <QVector2D>

#include <proj_api.h>

#define DEG2RAD   (3.14159265358979323846 / 180)
#define RAD2DEG   (180 / 3.14159265358979323846)

CrayfishViewer::~CrayfishViewer(){

    //std::cerr << "CF: terminating!" << std::endl;

    delete mMesh;
    mMesh = 0;

    delete mBBoxes;
    mBBoxes = 0;

    if(mImage){
        delete mImage;
        mImage = 0;
    }

    delete[] mE4Qtmp;
    mE4Qtmp = 0;

    delete [] mE4QtmpIndex;
    mE4QtmpIndex = 0;

    if(mProjNodes){
        delete[] mProjNodes;
        mProjNodes = 0;
    }
    if(mProjBBoxes){
        delete[] mProjBBoxes;
        mProjBBoxes = 0;
    }
}

CrayfishViewer::CrayfishViewer( QString twoDMFileName )
  : mImage(new QImage(0, 0, QImage::Format_ARGB32))
  , mCanvasWidth(0)
  , mCanvasHeight(0)
  , mLlX(0.0), mLlY(0.0)
  , mUrX(0.0), mUrY(0.0)
  , mPixelSize(0.0)
  , mRenderMesh(0)
  , mMeshColor(Qt::black)
  , mCurDataSetIdx(0)
  , mMesh(0)
  , mE4Qtmp(0)
  , mE4QtmpIndex(0)
  , mBBoxes(0)
  , mProjection(false)
  , mProjNodes(0)
  , mProjBBoxes(0)
{
  mMesh = Crayfish::loadMesh(twoDMFileName, &mLoadStatus);
  if (!mMesh)
    return;

  computeMeshExtent();

  // In order to keep things running quickly, we pre-compute many
  // element properties to speed up drawing at the expenses of memory.

  // Element bounding box (xmin, xmax and friends)

  Mesh::Nodes& nodes = mMesh->nodes();
  Mesh::Elements& elements = mMesh->elements();

  mBBoxes = new BBox[elements.count()];

  int E4Qcount = mMesh->elementCountForType(Element::E4Q);
  mE4Qtmp = new E4Qtmp[E4Qcount];
  mE4QtmpIndex = new int[elements.count()];
  memset(mE4QtmpIndex, -1, sizeof(int)*elements.count());
  int e4qIndex = 0;

  int i = 0;
  for (Mesh::Elements::iterator it = elements.begin(); it != elements.end(); ++it, ++i)
  {
    if( it->isDummy() )
      continue;

    Element& elem = *it;

    updateBBox(mBBoxes[i], elem, nodes.constData());

    if (elem.eType == Element::E4Q)
    {
      // cache some temporary data for faster rendering
      mE4QtmpIndex[i] = e4qIndex;
      E4Qtmp& e4q = mE4Qtmp[e4qIndex];

      E4Q_computeMapping(elem, e4q, nodes.constData());
      e4qIndex++;
    }
  }
}


void CrayfishViewer::computeMeshExtent()
{
    const Mesh::Nodes& nodes = mMesh->nodes();

    mXMin = nodes[0].x;
    mXMax = nodes[0].x;
    mYMin = nodes[0].y;
    mYMax = nodes[0].y;

    for (int i = 0; i < nodes.count(); i++)
    {
        const Node& n = nodes[i];
        if(n.x > mXMax) mXMax = n.x;
        if(n.x < mXMin) mXMin = n.x;
        if(n.y > mYMax) mYMax = n.y;
        if(n.y < mYMin) mYMin = n.y;
    }
}


bool CrayfishViewer::loadDataSet(QString fileName)
{
  Mesh::DataSets lst = Crayfish::loadDataSet(fileName, mMesh, &mLoadStatus);
  mMesh->dataSets() << lst;
  return lst.count();
}


bool CrayfishViewer::isDataSetLoaded(QString fileName)
{
  for (int i = 0; i < mMesh->dataSets().count(); ++i)
  {
    if (dataSet(i)->fileName() == fileName)
      return true;
  }
  return false;
}



void CrayfishViewer::setCanvasSize(const QSize& size)
{
  if(size.width() != mCanvasWidth || size.height() != mCanvasHeight){
      // The size of the canvas has changed so we need to re-allocate out QImage
      delete mImage;
      mImage = new QImage(size, QImage::Format_ARGB32);
  }
  mCanvasWidth = size.width();
  mCanvasHeight = size.height();
}

QSize CrayfishViewer::canvasSize() const
{
  return QSize(mCanvasWidth, mCanvasHeight);
}

void CrayfishViewer::setExtent(double llX, double llY, double pixelSize)
{
  mLlX = llX;
  mLlY = llY;
  mPixelSize = pixelSize;

  mUrX = mLlX + (mCanvasWidth*mPixelSize);
  mUrY = mLlY + (mCanvasHeight*mPixelSize);
}

QRectF CrayfishViewer::extent() const
{
  return QRectF(QPointF(mLlX,mUrY), QPointF(mUrX,mLlY));
}

void CrayfishViewer::setMeshRenderingEnabled(bool enabled)
{
  mRenderMesh = enabled;
}

bool CrayfishViewer::isMeshRenderingEnabled() const
{
  return mRenderMesh;
}

void CrayfishViewer::setMeshColor(const QColor& color)
{
  mMeshColor = color;
}

QColor CrayfishViewer::meshColor() const
{
  return mMeshColor;
}

void CrayfishViewer::setCurrentDataSetIndex(int index)
{
  mCurDataSetIdx = index;
}

int CrayfishViewer::currentDataSetIndex() const
{
  return mCurDataSetIdx;
}

const DataSet* CrayfishViewer::dataSet(int dataSetIndex) const
{
  if (dataSetIndex < 0 || dataSetIndex >= mMesh->dataSets().count())
    return 0;

  return mMesh->dataSets().at(dataSetIndex);
}

const DataSet *CrayfishViewer::currentDataSet() const
{
  return dataSet(mCurDataSetIdx);
}

void CrayfishViewer::setNoProjection()
{
  if (!mProjection)
    return; // nothing to do

  delete [] mProjNodes;
  mProjNodes = 0;
  delete [] mProjBBoxes;
  mProjBBoxes = 0;

  const Mesh::Elements& elems = mMesh->elements();
  for (int i = 0; i < elems.count(); ++i)
  {
    const Element& elem = elems[i];
    if (elem.eType == Element::E4Q)
    {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mMesh->nodes().constData());
    }
  }

  mProjection = false;
  mSrcProj4.clear();
  mDestProj4.clear();
}

bool CrayfishViewer::setProjection(const QString& srcProj4, const QString& destProj4)
{
  Q_ASSERT(!srcProj4.isEmpty() && !destProj4.isEmpty());

  if (mSrcProj4 == srcProj4 && mDestProj4 == destProj4)
    return true; // nothing has changed - so do nothing!

  mProjection = true;
  mSrcProj4 = srcProj4;
  mDestProj4 = destProj4;

  projPJ projSrc = pj_init_plus(srcProj4.toAscii().data());
  if (!projSrc)
  {
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  projPJ projDst = pj_init_plus(destProj4.toAscii().data());
  if (!projDst)
  {
    pj_free(projSrc);
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  const Mesh::Nodes& nodes = mMesh->nodes();

  if (mProjNodes == 0)
    mProjNodes = new Node[nodes.count()];

  memcpy(mProjNodes, mMesh->nodes().constData(), sizeof(Node)*nodes.count());

  if (pj_is_latlong(projSrc))
  {
    // convert source from degrees to radians
    for (int i = 0; i < nodes.count(); ++i)
    {
      mProjNodes[i].x *= DEG2RAD;
      mProjNodes[i].y *= DEG2RAD;
    }
  }

  int res = pj_transform(projSrc, projDst, nodes.count(), 3, &mProjNodes->x, &mProjNodes->y, NULL);

  if (res != 0)
  {
    qDebug("Crayfish: reprojection failed (%s)", pj_strerrno(res));
    setNoProjection();
    return false;
  }

  if (pj_is_latlong(projDst))
  {
    // convert source from degrees to radians
    const Mesh::Nodes& nodes = mMesh->nodes();
    for (int i = 0; i < nodes.count(); ++i)
    {
      mProjNodes[i].x *= RAD2DEG;
      mProjNodes[i].y *= RAD2DEG;
    }
  }

  pj_free(projSrc);
  pj_free(projDst);

  const Mesh::Elements& elems = mMesh->elements();

  if (mProjBBoxes == 0)
    mProjBBoxes = new BBox[elems.count()];

  for (int i = 0; i < elems.count(); ++i)
  {
    const Element& elem = elems[i];
    updateBBox(mProjBBoxes[i], elem, mProjNodes);

    if (elem.eType == Element::E4Q)
    {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mProjNodes); // update interpolation coefficients
    }
  }

  return true;
}

bool CrayfishViewer::hasProjection() const
{
  return mProjection;
}

void updateBBox(BBox& bbox, const Element& elem, const Node* nodes)
{
  const Node& node0 = nodes[elem.p[0]];

  bbox.minX = node0.x;
  bbox.minY = node0.y;
  bbox.maxX = node0.x;
  bbox.maxY = node0.y;

  for (int j = 1; j < elem.nodeCount(); ++j)
  {
    const Node& n = nodes[elem.p[j]];
    if (n.x < bbox.minX) bbox.minX = n.x;
    if (n.x > bbox.maxX) bbox.maxX = n.x;
    if (n.y < bbox.minY) bbox.minY = n.y;
    if (n.y > bbox.maxY) bbox.maxY = n.y;
  }

  bbox.maxSize = std::max( (bbox.maxX - bbox.minX),
                           (bbox.maxY - bbox.minY) );

}


QImage* CrayfishViewer::draw(){

    // Some sanity checks

    const DataSet* ds = currentDataSet();
    if (!ds)
      return 0;

    const Output* output = ds->currentOutput();
    if ( !output )
        return 0;

    mImage->fill( qRgba(255,255,255,0) );

    if(ds->isContourRenderingEnabled())
        renderContourData(ds, output);

    if (mRenderMesh)
        renderMesh();

    if(ds->isVectorRenderingEnabled() && ds->type() == DataSetType::Vector)
        renderVectorData(ds, output);

    return mImage;
}


void CrayfishViewer::renderContourData(const DataSet* ds, const Output* output)
{
        // Render E4Q before E3T
        QVector<Element::Type> typesToRender;
        typesToRender.append(Element::E4Q);
        typesToRender.append(Element::E3T);
        QVectorIterator<Element::Type> it(typesToRender);
        while(it.hasNext()){

            Element::Type elemTypeToRender = it.next();

            const Mesh::Elements& elems = mMesh->elements();
            for(int i = 0; i < elems.count(); i++){

                const Element& elem = elems[i];
                if( elem.eType != elemTypeToRender )
                    continue;

                if( elem.isDummy() )
                    continue;

                // For each element

                // If the element's activity flag is off, ignore it
                if( ! output->statusFlags[i] ){
                    continue;
                }

                // If the element is outside the view of the canvas, skip it
                if( elemOutsideView(i) ){
                    continue;
                }

                //
                const BBox& bbox = (mProjection ? mProjBBoxes[i] : mBBoxes[i]);
#if 0
                if( bbox.maxSize < mPixelSize ){
                    // The element is smaller than the pixel size so there is no point rendering the element properly
                    // Just take the value of the first point associated with the element instead
                    QPoint pp = realToPixel( elem.p[0] );
                    pp.setX( std::min(pp.x(), mCanvasWidth-1) );
                    pp.setX( std::max(pp.x(), 0) );
                    pp.setY( std::min(pp.y(), mCanvasHeight-1) );
                    pp.setY( std::max(pp.y(), 0) );

                    QRgb* line = (QRgb*) mImage->scanLine(pp.y());
                    float val = output->values[ elem.p[0] ];
                    line[pp.x()] = ds->contourColorMap().value(val);

                }else
#endif
                {
                    // Get the BBox of the element in pixels
                    QPoint ll = realToPixel(bbox.minX, bbox.minY);
                    QPoint ur = realToPixel(bbox.maxX, bbox.maxY);
                    int topLim = std::max( ur.y(), 0 );
                    int bottomLim = std::min( ll.y(), mCanvasHeight-1 );
                    int leftLim = std::max( ll.x(), 0 );
                    int rightLim = std::min( ur.x(), mCanvasWidth-1 );

                    for(int j=topLim; j<=bottomLim; j++){ // FIXME - are we missing the last line?  Should this be j<=bottomLim ?
                        paintRow(i, j, leftLim, rightLim, ds, output);
                    }
                }
            } // for all elements

        } // for element types
}


void CrayfishViewer::renderVectorData(
    const DataSet* ds,
    const Output* output)
{
    VectorLengthMethod shaftLengthCalculationMethod = ds->vectorShaftLengthMethod();
    float minShaftLength   = ds->vectorShaftLengthMin();
    float maxShaftLength   = ds->vectorShaftLengthMax();
    float scaleFactor      = ds->vectorShaftLengthScaleFactor();
    float fixedShaftLength = ds->vectorShaftLengthFixed();
    int lineWidth          = ds->vectorPenWidth();
    float vectorHeadWidthPerc  = ds->vectorHeadWidth();
    float vectorHeadLengthPerc = ds->vectorHeadLength();

        /*
          Here is where we render vector data

          Vectors will either be rendered at nodes or on a grid spacing specified by the user.
          In the latter case, the X and Y components will need to be interpolated

          In the case of rendering vectors at nodes:
            Loop through all nodes:
                If node is within the current screen extent:
                    Render it:
                        Get the X and Y components
                        Turn those compnents into pixel distances
                        Render an arrow from the node
        */

        // Set up the render configuration options

        // Determine the min and max magnitudes in this layer
        float minVal = ds->minZValue();
        float maxVal = ds->maxZValue();

        // Get a list of nodes that are within the current render extent
        std::vector<int> candidateNodes;

        const Mesh::Nodes& nodes = mMesh->nodes();
        for(int i = 0; i < nodes.count(); i++)
        {
            if (nodeInsideView(i))
                candidateNodes.push_back( i );
        }


        QPainter p;
        p.begin(mImage);
        p.setRenderHint(QPainter::Antialiasing);
        p.setBrush( Qt::SolidPattern );
        QPen pen = p.pen();
        pen.setCapStyle(Qt::FlatCap);
        pen.setJoinStyle(Qt::MiterJoin);
        pen.setWidth( lineWidth );
        p.setPen(pen);

        // Make a set of vector head coordinates that we will place at the end of each vector,
        // scale, translate and rotate.
        QPointF vectorHeadPoints[3];
        QPointF finalVectorHeadPoints[3];

        // First head point:  top of ->
        vectorHeadPoints[0].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
        vectorHeadPoints[0].setY( vectorHeadWidthPerc * 0.5 * 0.01 );

        // Second head point:  right of ->
        vectorHeadPoints[1].setX(0.0);
        vectorHeadPoints[1].setY(0.0);

        // Third head point:  bottom of ->
        vectorHeadPoints[2].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
        vectorHeadPoints[2].setY( -1.0 * vectorHeadWidthPerc * 0.5 * 0.01 );

        for(uint i=0; i<candidateNodes.size(); i++){
            // Get the value
            uint nodeIndex = candidateNodes.at(i);

            float xVal = output->values_x[nodeIndex];
            float yVal = output->values_y[nodeIndex];
            float V = output->values[nodeIndex];  // pre-calculated magnitude

            if(xVal == 0.0 && yVal == 0.0){
                continue;
            }

            // Now determine the X and Y distances of the end of the line from the start

            float xDist = 0.0;
            float yDist = 0.0;

            // Determine the angle of the vector, counter-clockwise, from east
            // (and associated trigs)
            double vectorAngle = -1.0 * atan( (-1.0 * yVal) / xVal );
            double cosAlpha = cos( vectorAngle ) * mag(xVal);
            double sinAlpha = sin( vectorAngle ) * mag(xVal);

            if(shaftLengthCalculationMethod == MinMax){
                double k = (V - minVal) / (maxVal - minVal);
                double L = minShaftLength + k * (maxShaftLength - minShaftLength);
                xDist = cosAlpha * L;
                yDist = sinAlpha * L;
            }else if(shaftLengthCalculationMethod == Scaled){
                xDist = scaleFactor * xVal;
                yDist = scaleFactor * yVal;
            }else{
                // We must be using a fixed length
                xDist = cosAlpha * fixedShaftLength;
                yDist = sinAlpha * fixedShaftLength;
            }

            // Flip the Y axis (pixel vs real-world axis)
            yDist *= -1.0;

            if(qAbs(xDist) < 1 && qAbs(yDist) < 1){
                continue;
            }

            // Determine the line coords
            QPointF lineStart = realToPixelF( nodeIndex );
            QPointF lineEnd = QPointF( lineStart.x() + xDist,
                                       lineStart.y() + yDist);

            float vectorLength = sqrt( pow(lineEnd.x() - lineStart.x(), 2) + pow(lineEnd.y() - lineStart.y(), 2) );

            // Check to see if any of the coords are outside the QImage area, if so, skip the whole vector
            if( lineStart.x() < 0 ||
                lineStart.x() > mCanvasWidth ||
                lineStart.y() < 0 ||
                lineStart.y() > mCanvasHeight ||
                lineEnd.x() < 0 ||
                lineEnd.x() > mCanvasWidth ||
                lineEnd.y() < 0 ||
                lineEnd.y() > mCanvasHeight ){

                continue;
            }

            // Determine the arrow head coords
            for(int j=0; j<3; j++){

                finalVectorHeadPoints[j].setX(   lineEnd.x()
                                               + ( vectorHeadPoints[j].x() * cosAlpha * vectorLength )
                                               - ( vectorHeadPoints[j].y() * sinAlpha * vectorLength )
                                             );

                finalVectorHeadPoints[j].setY(   lineEnd.y()
                                               - ( vectorHeadPoints[j].x() * sinAlpha * vectorLength )
                                               - ( vectorHeadPoints[j].y() * cosAlpha * vectorLength )
                                             );
            }

            // Now actually draw the vector
            p.drawLine(lineStart, lineEnd);
            p.drawPolygon( (const QPointF*)&finalVectorHeadPoints, 3);
            bool debug = false;
            if(debug){
                // Write the ID of the node next to the vector...
                QPointF tp;
                tp.setX( lineEnd.x() + 10.0 );
                tp.setY( lineEnd.y() - 10.0 );
                QString nodeText;
                nodeText.setNum(nodeIndex);
                p.drawText( tp, nodeText );
            }

        }
        p.end();
}


void CrayfishViewer::renderMesh()
{
      // render mesh as a wireframe

      QPainter p(mImage);
      p.setPen(mMeshColor);
      QPoint pts[5];
      const Mesh::Elements& elems = mMesh->elements();
      for (int i=0; i < elems.count(); ++i)
      {
        const Element& elem = elems[i];
        if( elem.isDummy() )
            continue;

        // If the element is outside the view of the canvas, skip it
        if( elemOutsideView(i) )
            continue;

        if (elem.eType == Element::E4Q)
        {
          pts[0] = pts[4] = realToPixel( elem.p[0] ); // first and last point
          pts[1] = realToPixel( elem.p[1] );
          pts[2] = realToPixel( elem.p[2] );
          pts[3] = realToPixel( elem.p[3] );
          p.drawPolyline(pts, 5);
        }
        else if (elem.eType == Element::E3T)
        {
          pts[0] = pts[3] = realToPixel( elem.p[0] ); // first and last point
          pts[1] = realToPixel( elem.p[1] );
          pts[2] = realToPixel( elem.p[2] );
          p.drawPolyline(pts, 4);
        }
      }
}

QPoint CrayfishViewer::realToPixel(int nodeIndex){
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mMesh->nodes()[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPoint CrayfishViewer::realToPixel(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = mCanvasHeight - (y - mLlY) / mPixelSize;
    return QPoint(px, py);
}

QPointF CrayfishViewer::realToPixelF(int nodeIndex){
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mMesh->nodes()[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPointF CrayfishViewer::realToPixelF(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = float(mCanvasHeight) - (y - mLlY) / mPixelSize;
    return QPointF(px, py);
}

void CrayfishViewer::paintRow(uint elementIdx, int rowIdx, int leftLim, int rightLim, const DataSet* ds, const Output* output){
    /*
      Grab the pointer to the row if we do not have it already
      */
    QRgb* line = (QRgb*) mImage->scanLine(rowIdx);

    for(int j=leftLim; j<=rightLim; j++){
        // Determine real-world coords
        // Interpolate a value from the element
        // Set the value in the QImage
        QPointF p = pixelToReal(j, rowIdx);

        double val;
        if( interpolatValue(elementIdx, p.x(), p.y(), &val, output) ){
            // The supplied point was inside the element
            line[j] = ds->contourColorMap().value(val);
        }
    }
}


bool CrayfishViewer::nodeInsideView(uint nodeIndex)
{
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mMesh->nodes()[nodeIndex]);
  return n.x > mLlX && n.x < mUrX && n.y > mLlY && n.y < mUrY;
}

bool CrayfishViewer::elemOutsideView(uint i){
  const BBox& bbox = (mProjection ? mProjBBoxes[i] : mBBoxes[i]);
  // Determine if this element is visible within the view
  return bbox.maxX < mLlX || bbox.minX > mUrX || bbox.minY > mUrY || bbox.maxY < mLlY;
}

bool CrayfishViewer::interpolatValue(uint elementIndex, double x, double y, double* interpolatedVal, const Output* output){

    const Element& elem = mMesh->elements()[elementIndex];

    if(elem.eType == Element::E4Q){

        int e4qIndex = mE4QtmpIndex[elementIndex];
        E4Qtmp& e4q = mE4Qtmp[e4qIndex];

        double Lx, Ly;
        if (!E4Q_mapPhysicalToLogical(e4q, x, y, Lx, Ly))
          return false;

        if (Lx < 0 || Ly < 0 || Lx > 1 || Ly > 1)
          return false;

        double q11 = output->values[ elem.p[2] ];
        double q12 = output->values[ elem.p[1] ];
        double q21 = output->values[ elem.p[3] ];
        double q22 = output->values[ elem.p[0] ];

        *interpolatedVal = q11*Lx*Ly + q21*(1-Lx)*Ly + q12*Lx*(1-Ly) + q22*(1-Lx)*(1-Ly);

        return true;

    }else if(elem.eType == Element::E3T){

        /*
            So - we're interpoalting a 3-noded triangle
            The query point must be within the bounding box of this triangl but not nessisarily
            within the triangle itself.
          */

        /*
          First determine if the point of interest lies within the triangle using Barycentric techniques
          described here:  http://www.blackpawn.com/texts/pointinpoly/
          */

        const Node* nodes = mProjection ? mProjNodes : mMesh->nodes().constData();
        QPointF pA(nodes[elem.p[0]].toPointF());
        QPointF pB(nodes[elem.p[1]].toPointF());
        QPointF pC(nodes[elem.p[2]].toPointF());

        if (pA == pB || pA == pC || pB == pC)
          return false; // this is not a valid triangle!

        QPointF pP(x, y);

        // Compute vectors
        QVector2D v0( pC - pA );
        QVector2D v1( pB - pA );
        QVector2D v2( pP - pA );

        // Compute dot products
        double dot00 = QVector2D::dotProduct(v0, v0);
        double dot01 = QVector2D::dotProduct(v0, v1);
        double dot02 = QVector2D::dotProduct(v0, v2);
        double dot11 = QVector2D::dotProduct(v1, v1);
        double dot12 = QVector2D::dotProduct(v1, v2);

        // Compute barycentric coordinates
        double invDenom = 1.0 / (dot00 * dot11 - dot01 * dot01);
        double lam1 = (dot11 * dot02 - dot01 * dot12) * invDenom;
        double lam2 = (dot00 * dot12 - dot01 * dot02) * invDenom;
        double lam3 = 1.0 - lam1 - lam2;

        // Return if POI is outside triangle
        if( (lam1 < 0) || (lam2 < 0) || (lam3 < 0) ){
            return false;
        }

        // Now interpolate

        double z1 = output->values[ elem.p[0] ];
        double z2 = output->values[ elem.p[1] ];
        double z3 = output->values[ elem.p[2] ];
        *interpolatedVal = lam1 * z3 + lam2 * z2 + lam3 * z1;
        return true;

    }else{
      Q_ASSERT(0 && "unknown element type");
      return false;
    }
}

QPointF CrayfishViewer::pixelToReal(int i, int j){
    double x = mLlX + (i * mPixelSize);
    // double y = mCanvasHeight - (mLlY + (j * mPixelSize));
    // TODO: shouldn't this be without "-1" ???
    double y = mLlY + mPixelSize * (mCanvasHeight-1-j);
    return QPointF(x,y);
}

double CrayfishViewer::valueAtCoord(const Output* output, double xCoord, double yCoord)
{
    if (!output)
      return -9999.0;

    /*
      We want to find the value at the given coordinate
      */

    /*
        Loop through all the elements in the dataset and make a list of those
      */

    std::vector<uint> candidateElementIds;

    const Mesh::Elements& elems = mMesh->elements();
    for (int i = 0; i < elems.count(); i++)
    {

        const BBox& bbox = (mProjection ? mProjBBoxes[i] : mBBoxes[i]);
        if( bbox.isPointInside(xCoord, yCoord) ){

            candidateElementIds.push_back(i);
        }
    }

    if( candidateElementIds.size() == 0 ){
        return -9999.0;
    }

    double value;

    for(uint i=0; i<candidateElementIds.size(); i++){

        uint elemIndex = candidateElementIds.at(i);
        if( ! output->statusFlags[elemIndex] ){
            continue;
        }
        if( interpolatValue(elemIndex, xCoord, yCoord, &value, output) ){
            // We successfully got a value, return it and leave
            return value;
        }
    }

    return -9999.0;
}


bool CrayfishViewer::exportRawDataToTIF(int dataSetIndex, int outputTime, double mupp, const QString& outFilename, const QString& projWkt)
{
  RawData* rd = exportRawData(dataSetIndex, outputTime, mupp);
  if (!rd)
    return false;

  bool res = CrayfishGDAL::writeGeoTIFF(outFilename, rd, projWkt);
  delete rd;

  return res;
}


RawData* CrayfishViewer::exportRawData(int dataSetIndex, int outputTime, double mupp)
{
  const DataSet* ds = dataSet(dataSetIndex);
  if (!ds)
    return 0;
  const Output* output = ds->output(outputTime);
  if (!output)
    return 0;
  if (mupp <= 0)
    return 0;

  // keep one pixel around
  // e.g. if we have mesh with coords 0..10 with sampling of 1, then we actually need 11 pixels
  double xMin = mXMin - mupp;
  double xMax = mXMax + mupp;
  double yMin = mYMin - mupp;
  double yMax = mYMax + mupp;

  // calculate transform
  // (uses envelope of the mesh)
  int imgWidth = ceil((xMax - xMin) / mupp);
  int imgHeight = ceil((yMax - yMin) / mupp);
  if (!imgWidth || !imgHeight)
    return 0;
  MapToPixel xform(xMin, yMin, mupp, imgHeight);

  // prepare geometry transform
  yMax = yMin + imgHeight*mupp;  // this is different from yMax previously - due to using fixed pixel size
  // also shift the exported raster by half of pixel size in both directions
  // sampled value for X needs to occupy interval (X-mupp/2,X+mupp/2) - without the shift the value would be misaligned to (X,X+mupp)
  QVector<double> geo;
  geo << xMin - mupp/2 << mupp << 0
      << yMax + mupp/2 << 0    << -mupp;

  RawData* rd = new RawData(imgWidth, imgHeight, geo);

  // First export quads, then triangles.
  // We use this ordering because from 1D simulation we will get tesselated river polygons from linestrings
  // and we want them to be on top of the terrain (quads)
  exportRawDataElements(Element::E4Q, output, rd, xform);
  exportRawDataElements(Element::E3T, output, rd, xform);

  return rd;
}

void CrayfishViewer::exportRawDataElements(Element::Type elemType, const Output* output, RawData* rd, const MapToPixel& xform)
{
  const Mesh::Elements& elems = mMesh->elements();
  for (int i=0; i < elems.count(); i++)
  {
    const Element& elem = elems[i];
    if(elem.eType != elemType)
      continue;

    if (elem.isDummy())
      continue;

    // If the element's activity flag is off, ignore it
    if(!output->statusFlags[i])
      continue;

    const BBox& bbox = mBBoxes[i];

    // Get the BBox of the element in pixels
    QPointF ll = xform.realToPixel(bbox.minX, bbox.minY);
    QPointF ur = xform.realToPixel(bbox.maxX, bbox.maxY);

    // TODO: floor/ceil ?
    int topLim = ur.y();
    int bottomLim = ll.y();
    int leftLim = ll.x();
    int rightLim = ur.x();

    double val;
    for (int j=topLim; j<=bottomLim; j++)
    {
      float* line = rd->scanLine(j);
      for (int k=leftLim; k<=rightLim; k++)
      {
        Q_ASSERT(k >= 0 && k < rd->cols());
        QPointF p = xform.pixelToReal(k, j);
        if( interpolatValue(i, p.x(), p.y(), &val, output) )
            line[k] = val; // The supplied point was inside the element
      }
    }
  }
}
