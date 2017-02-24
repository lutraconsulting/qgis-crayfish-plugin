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


#include <stdlib.h>
#include <time.h>
#include <algorithm>

#include "crayfish_renderer.h"

#include "crayfish_dataset.h"
#include "crayfish_mesh.h"
#include "crayfish_output.h"
#include "crayfish_trace.h"

#include <QMutex>
#include <QImage>
#include <QPainter>
#include <QVector2D>
#include <QPolygonF>
#include <QPainterPath>

static QMutex mutex;

Renderer::Renderer(const RendererConfig& cfg, QImage& img)
    : mCfg(cfg)
    , mtp(cfg.llX, cfg.llY, cfg.pixelSize, cfg.outputSize.height())
    , mImage(img)
{
    mLlX = cfg.llX;
    mLlY = cfg.llY;
    mPixelSize = cfg.pixelSize;
    mOutputSize = cfg.outputSize;

    mUrX = mLlX + (mOutputSize.width()*mPixelSize);
    mUrY = mLlY + (mOutputSize.height()*mPixelSize);

    mOutputContour = cfg.outputContour;
    mOutputVector  = cfg.outputVector;
    mMesh = cfg.outputMesh;

    if (mOutputContour)
    {
        if (!mOutputContour->dataSet)
        {
            qDebug("Ignoring contour data: no dataset");
            mOutputContour = 0;
        }
        else if (mOutputContour->dataSet->mesh() != mMesh)
        {
            qDebug("Ignoring contour data: different mesh");
            mOutputContour = 0;
        }
    }

    if (mOutputVector)
    {
        if (!mOutputVector->dataSet)
        {
            qDebug("Ignoring vector data: no dataset");
            mOutputVector = 0;
        }
        else if (mOutputVector->dataSet->mesh() != mMesh)
        {
            qDebug("Ignoring vector data: different mesh");
            mOutputVector = 0;
        }
    }

    // use a default color map if none specified
    if (mOutputContour && mCfg.ds.mColorMap.items.count() == 0 && mOutputContour->dataSet)
    {
        double vMin = mOutputContour->dataSet->minZValue();
        double vMax = mOutputContour->dataSet->maxZValue();
        mCfg.ds.mColorMap = ColorMap::defaultColorMap(vMin, vMax);
    }
}

void Renderer::validateCache() {

    mutex.lock();

    mMesh->getTraceCache()->validateCache(this->mCfg);

    mutex.unlock();
}

void Renderer::draw()
{
    if (!mMesh)
        return; // nothing to do

    if (mCfg.mesh.mRenderMesh && mCfg.mesh.mMeshFillEnabled)
        drawMeshFill();

    if (mOutputContour)
        drawContourData(mOutputContour);

    if (mCfg.mesh.mRenderMesh)
        drawMeshFrame();

    if (mCfg.mesh.mRenderMesh && mCfg.mesh.mMeshElemLabel)
        drawMeshLabels();

    if (mOutputVector && mOutputVector->dataSet->type() == DataSet::Vector)
        drawVectorData(mOutputVector);
}

QPolygonF Renderer::elementPolygonPixel(const Element& elem)
{
    int nPoints = elem.nodeCount();
    QPolygonF pts(nPoints + 1);
    for (int i=0; i<nPoints; ++i)
    {
        pts[i] = realToPixel( elem.p(i) );
    }

    if (elem.eType() == Element::E2L)
    {
        pts.resize(nPoints); //remove last one
    } else {
        pts[nPoints] = pts[0]; // last one == first one
    }

    return pts;
}

void Renderer::drawMeshFill()
{
    QPainter p(&mImage);
    p.setRenderHint(QPainter::Antialiasing);
    QBrush fillBrush(mCfg.mesh.mMeshFillColor);

    const Mesh::Elements& elems = mMesh->elements();
    for (int i=0; i < elems.count(); ++i)
    {
        const Element& elem = elems[i];

        if( elem.isDummy() )
            continue;

        // If the element is outside the view of the canvas, skip it
        if( elemOutsideView(i) )
            continue;

        QPolygonF pts = elementPolygonPixel(elem);

        QPainterPath elemPath;
        elemPath.addPolygon(pts);
        p.fillPath(elemPath, fillBrush);
    }
}

void Renderer::drawMeshFrame()
{
    QPainter p(&mImage);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QBrush(mCfg.mesh.mMeshBorderColor), mCfg.mesh.mMeshBorderWidth));

    const Mesh::Elements& elems = mMesh->elements();
    for (int i=0; i < elems.count(); ++i)
    {
        const Element& elem = elems[i];
        if( elem.isDummy() )
            continue;

        // If the element is outside the view of the canvas, skip it
        if( elemOutsideView(i) )
            continue;

        QPolygonF pts = elementPolygonPixel(elem);

        p.drawPolyline(pts.constData(), pts.size());
    }
}

void Renderer::drawMeshLabels()
{
    QPainter p(&mImage);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QBrush(mCfg.mesh.mMeshBorderColor), mCfg.mesh.mMeshBorderWidth));
    p.setFont(QFont(""));
    const Mesh::Elements& elems = mMesh->elements();
    for (int i=0; i < elems.count(); ++i)
    {
        const Element& elem = elems[i];
        if( elem.isDummy() )
            continue;

        // If the element is outside the view of the canvas, skip it
        if( elemOutsideView(i) )
            continue;

        QPolygonF pts = elementPolygonPixel(elem);

        double cx, cy;
        mMesh->elementCentroid(i, cx, cy);
        QString txt = QString::number(elem.id());
        QRect bb = p.fontMetrics().boundingRect(txt);
        QPointF xy = mtp.realToPixel(cx, cy);
        bb.moveTo(xy.x() - bb.width()/2.0, xy.y() - bb.height()/2.0);

        if (pts.containsPoint(bb.bottomLeft(), Qt::WindingFill) &&
                pts.containsPoint(bb.bottomRight(), Qt::WindingFill) &&
                pts.containsPoint(bb.topLeft(), Qt::WindingFill) &&
                pts.containsPoint(bb.topRight(), Qt::WindingFill))
        {
            p.drawText(bb, Qt::AlignCenter, txt);
        }
    }
}

void Renderer::drawContourData(const Output* output)
{
    // Render E4Q before E3T
    QVector<Element::Type> typesToRender;
    typesToRender.append(Element::ENP);
    typesToRender.append(Element::E4Q);
    typesToRender.append(Element::E3T);
    typesToRender.append(Element::E2L);
    QVectorIterator<Element::Type> it(typesToRender);
    while(it.hasNext())
    {
        Element::Type elemTypeToRender = it.next();

        const Mesh::Elements& elems = mMesh->elements();
        for(int i = 0; i < elems.count(); i++){

            const Element& elem = elems[i];
            if( elem.eType() != elemTypeToRender )
                continue;

            if( elem.isDummy() )
                continue;

            // For each element

            // If the element's activity flag is off, ignore it
            if( ! output->isActive(i) ){
                continue;
            }

            // If the element is outside the view of the canvas, skip it
            if( elemOutsideView(i) ){
                continue;
            }

            if (elem.eType() == Element::E2L) {
                paintLine(elem, output);
            } else {
                const BBox& bbox = mMesh->projectedBBox(i);

                // Get the BBox of the element in pixels
                int topLim, bottomLim, leftLim, rightLim;
                bbox2rect(bbox, leftLim, rightLim, topLim, bottomLim);

                for(int j=topLim; j<=bottomLim; j++)
                {
                    paintRow(i, j, leftLim, rightLim, output);
                }
            }
        } // for all elements

    } // for element types
}


inline float mag(float input)
{
    if(input < 0.0){
        return -1.0;
    }
    return 1.0;
}

void Renderer::drawVectorData(const Output* output)
{
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
    QPainter p(&mImage);
    p.setRenderHint(QPainter::Antialiasing);
    QPen pen = p.pen();
    pen.setCapStyle(Qt::FlatCap);
    pen.setJoinStyle(Qt::MiterJoin);
    pen.setWidth(mCfg.ds.mLineWidth);
    pen.setColor(mCfg.ds.mVectorColor);
    p.setPen(pen);

    if (mCfg.ds.mVectorTrace) {
        validateCache();

        if (mCfg.ds.mVectorTraceFPS > 0)
            drawVectorDataAsTrace(p);
        else
            drawVectorDataStreamLines(p);

    } else {
        if (mCfg.ds.mVectorUserGrid)
            drawVectorDataOnGrid(p, output);
        else
        {
            if (output->type() == Output::TypeNode)
                drawVectorDataOnNodes(p, static_cast<const NodeOutput*>(output));
            else
                drawVectorDataOnElements(p, static_cast<const ElementOutput*>(output));
        }
        p.end();
    }
}


void Renderer::drawVectorDataOnGrid(QPainter& p, const Output* output)
{
    int cellx = mCfg.ds.mVectorUserGridCellSize.width();
    int celly = mCfg.ds.mVectorUserGridCellSize.height();

    const Mesh::Elements& elems = mMesh->elements();
    for(int i = 0; i < elems.count(); i++)
    {
        const Element& elem = elems[i];

        if (elem.isDummy())
            continue;

        // If the element's activity flag is off, ignore it
        if (!output->isActive(i))
            continue;

        // If the element is outside the view of the canvas, skip it
        if (elemOutsideView(i))
            continue;

        const BBox& bbox = mMesh->projectedBBox(i);

        // Get the BBox of the element in pixels
        int left, right, top, bottom;
        bbox2rect(bbox, left, right, top, bottom);

        // Align rect to the grid (e.g. interval <13, 36> with grid cell 10 will be trimmed to <20,30>
        if (left % cellx != 0)
            left += cellx - (left % cellx);
        if (right % cellx != 0)
            right -= (right % cellx);
        if (top % celly != 0)
            top += celly - (top % celly);
        if (bottom % celly != 0)
            bottom -= (bottom % celly);

        for (int y = top; y <= bottom; y += celly)
        {
            for (int x = left; x <= right; x += cellx)
            {
                QPointF pt = mtp.pixelToReal(x, y);

                double vx, vy;
                if (mMesh->vectorValueAt(i, pt.x(), pt.y(), &vx, &vy, output))
                {
                    // The supplied point was inside the element
                    drawVectorArrow(p, output, QPointF(x,y), vx, vy);
                }

            }
        }
    } // for all elements
}


bool calcVectorLineEnd(QPointF& lineEnd, float& vectorLength, double& cosAlpha, double& sinAlpha, //out
                       const RendererConfig* cfg, const Output* output, const QPointF& lineStart, float xVal, float yVal, float* V /*=0*/ //in
                       ) {
    // return true on error

    if (xVal == 0.0 && yVal == 0.0)
        return true;

    // do not render if magnitude is outside of the filtered range (if filtering is enabled)
    float magnitude;
    if (V)
        magnitude = *V;
    else
        magnitude = sqrt(xVal*xVal + yVal*yVal);


    if (cfg->ds.mVectorFilterMin >= 0 && magnitude < cfg->ds.mVectorFilterMin)
        return true;
    if (cfg->ds.mVectorFilterMax >= 0 && magnitude > cfg->ds.mVectorFilterMax)
        return true;

    // Determine the angle of the vector, counter-clockwise, from east
    // (and associated trigs)
    double vectorAngle = -1.0 * atan( (-1.0 * yVal) / xVal );
    cosAlpha = cos( vectorAngle ) * mag(xVal);
    sinAlpha = sin( vectorAngle ) * mag(xVal);

    // Now determine the X and Y distances of the end of the line from the start
    float xDist = 0.0;
    float yDist = 0.0;
    switch (cfg->ds.mShaftLengthMethod)
    {
    case ConfigDataSet::MinMax:
    {
        float minShaftLength = cfg->ds.mMinShaftLength;
        float maxShaftLength = cfg->ds.mMaxShaftLength;
        float minVal = output->dataSet->minZValue();
        float maxVal = output->dataSet->maxZValue();
        double k = (magnitude - minVal) / (maxVal - minVal);
        double L = minShaftLength + k * (maxShaftLength - minShaftLength);
        xDist = cosAlpha * L;
        yDist = sinAlpha * L;
        break;
    }
    case ConfigDataSet::Scaled:
    {
        float scaleFactor = cfg->ds.mScaleFactor;
        xDist = scaleFactor * xVal;
        yDist = scaleFactor * yVal;
        break;
    }
    case ConfigDataSet::Fixed:
    {
        // We must be using a fixed length
        float fixedShaftLength = cfg->ds.mFixedShaftLength;
        xDist = cosAlpha * fixedShaftLength;
        yDist = sinAlpha * fixedShaftLength;
        break;
    }
    }

    // Flip the Y axis (pixel vs real-world axis)
    yDist *= -1.0;

    if (qAbs(xDist) < 1 && qAbs(yDist) < 1)
        return true;

    // Determine the line coords
    lineEnd = QPointF( lineStart.x() + xDist,
                       lineStart.y() + yDist);

    vectorLength = sqrt(xDist*xDist + yDist*yDist);

    // Check to see if any of the coords are outside the QImage area, if so, skip the whole vector
    if( lineStart.x() < 0 || lineStart.x() > cfg->outputSize.width() ||
            lineStart.y() < 0 || lineStart.y() > cfg->outputSize.height() ||
            lineEnd.x() < 0   || lineEnd.x() > cfg->outputSize.width() ||
            lineEnd.y() < 0   || lineEnd.y() > cfg->outputSize.height() )
        return true;

    return false; //success
}

void Renderer::drawVectorDataStreamLines(QPainter& p) {
    TraceRendererCache* cache = mMesh->getTraceCache();
    for (int i=0; i<cache->getStreamLinesCount(); ++i) {
        const TraceStreamLine& streamline = cache->getStreamLine(i);
        p.drawPolyline(streamline.data(), streamline.size());
    }
}

static void drawStreamLine(const RendererConfig& cfg, QPainter& p, const QVector<QColor>& colors, const TraceStreamLine& streamline, int start, int end, int color_idx) {
    for (int j=start; j<end; ++j) {
        const QPointF& startPoint = streamline.at(j-1);
        const QPointF& endPoint = streamline.at(j);

        QLinearGradient gradient;
        gradient.setStart(startPoint);
        gradient.setFinalStop(endPoint);
        gradient.setColorAt(0, colors.at((color_idx + j - 1) % cfg.ds.mVectorTraceAnimationSteps));
        gradient.setColorAt(1, colors.at((color_idx + j) % cfg.ds.mVectorTraceAnimationSteps));

        QPen pen = p.pen();
        pen.setBrush(QBrush(gradient));
        p.setPen(pen);

        p.drawLine(startPoint, endPoint);
    }
}

void Renderer::drawVectorDataAsTrace(QPainter& p) {
    QVector<QColor> colors;
    colors.append(QColor(Qt::transparent));

    for (int i=0; i<mCfg.ds.mVectorTraceAnimationSteps; ++i) {
        QColor c(mCfg.ds.mVectorColor);
        c.setAlphaF(i/float(mCfg.ds.mVectorTraceAnimationSteps));
        colors.append(c);
    }

    TraceRendererCache* cache = mMesh->getTraceCache();
    int iter = cache->getNextIteration();
    int color_iter = mCfg.ds.mVectorTraceAnimationSteps - iter % mCfg.ds.mVectorTraceAnimationSteps;

    for (int i=0; i<cache->getStreamLinesCount(); ++i) {
        const TraceStreamLine& streamline = cache->getStreamLine(i);
        int start, end;
        if (mCfg.ds.mVectorTraceParticles) {
            start = iter % streamline.size();
            end = start + mCfg.ds.mVectorTraceAnimationSteps;

            if (end <= streamline.size())
                drawStreamLine(mCfg, p, colors, streamline, start  + 1, end, color_iter);
            else {
                drawStreamLine(mCfg, p, colors, streamline, start  + 1, streamline.size(), color_iter);
                drawStreamLine(mCfg, p, colors, streamline, 1, std::min(end - streamline.size(), streamline.size()), color_iter);
            }
        } else {
            drawStreamLine(mCfg, p, colors, streamline, 1, streamline.size(), color_iter);
        }
    }
}


void Renderer::drawVectorDataOnNodes(QPainter& p, const NodeOutput* output)
{
    const Mesh::Nodes& nodes = mMesh->nodes();
    for(int nodeIndex = 0; nodeIndex < nodes.count(); nodeIndex++)
    {
        if (!nodeInsideView(nodeIndex))
            continue;

        float xVal = output->loadedValuesV()[nodeIndex].x;
        float yVal = output->loadedValuesV()[nodeIndex].y;
        float V = output->loadedValues()[nodeIndex];  // pre-calculated magnitude
        QPointF lineStart = realToPixelF( nodeIndex );

        drawVectorArrow(p, output, lineStart, xVal, yVal, &V);
    }
}

void Renderer::drawVectorDataOnElements(QPainter& p, const ElementOutput* output)
{
    const Mesh::Elements& elements = mMesh->elements();
    for(int elemIndex = 0; elemIndex < elements.count(); elemIndex++)
    {
        if (elemOutsideView(elemIndex))
            continue;

        double cx, cy;
        mMesh->elementCentroid(elemIndex, cx, cy);

        float xVal = output->loadedValuesV()[elemIndex].x;
        float yVal = output->loadedValuesV()[elemIndex].y;
        float V = output->loadedValues()[elemIndex];  // pre-calculated magnitude
        QPointF lineStart = mtp.realToPixel(cx, cy);

        drawVectorArrow(p, output, lineStart, xVal, yVal, &V);
    }
}


void Renderer::drawVectorArrow(QPainter& p, const Output* output, const QPointF& lineStart, float xVal, float yVal, float* V /*=0*/)
{
    QPointF lineEnd;
    float vectorLength;
    double cosAlpha, sinAlpha;
    if (calcVectorLineEnd(lineEnd, vectorLength, cosAlpha, sinAlpha,
                          &mCfg, output, lineStart, xVal, yVal, V))
        return;

    // Make a set of vector head coordinates that we will place at the end of each vector,
    // scale, translate and rotate.
    QPointF vectorHeadPoints[3];
    QPointF finalVectorHeadPoints[3];

    float vectorHeadWidthPerc  = mCfg.ds.mVectorHeadWidthPerc;
    float vectorHeadLengthPerc = mCfg.ds.mVectorHeadLengthPerc;

    // First head point:  top of ->
    vectorHeadPoints[0].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
    vectorHeadPoints[0].setY( vectorHeadWidthPerc * 0.5 * 0.01 );

    // Second head point:  right of ->
    vectorHeadPoints[1].setX(0.0);
    vectorHeadPoints[1].setY(0.0);

    // Third head point:  bottom of ->
    vectorHeadPoints[2].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
    vectorHeadPoints[2].setY( -1.0 * vectorHeadWidthPerc * 0.5 * 0.01 );

    // Determine the arrow head coords
    for (int j=0; j<3; j++)
    {
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

#if 0  // debug
    // Write the ID of the node next to the vector...
    QString nodeText;
    nodeText.setNum(nodeIndex);
    p.drawText(QPointF(lineEnd.x() + 10.0, lineEnd.y() - 10.0), nodeText);
#endif
}


void Renderer::paintRow(uint elementIdx, int rowIdx, int leftLim, int rightLim, const Output* output)
{
    /*
    Grab the pointer to the row if we do not have it already
    */
    QRgb* line = (QRgb*) mImage.scanLine(rowIdx);

    for(int j=leftLim; j<=rightLim; j++)
    {
        // Determine real-world coords
        // Interpolate a value from the element
        // Set the value in the QImage
        QPointF p = mtp.pixelToReal(j, rowIdx);

        double val;
        if( mMesh->valueAt(elementIdx, p.x(), p.y(), &val, output) )
        {
            // The supplied point was inside the element
            line[j] = mCfg.ds.mColorMap.value(val);
        }
    }
}

void Renderer::paintLine(const Element &elem, const Output* output)
{
    Q_ASSERT(elem.eType() == Element::E2L);

    QPoint pix0 = realToPixel( elem.p(0) );
    QPoint pix1 = realToPixel( elem.p(1) );

    // Gradient
    double val0 = mMesh->valueAt(elem.p(0), output);
    double val1 = mMesh->valueAt(elem.p(1), output);

    QColor color0(Qt::transparent);
    QColor color1(Qt::transparent);

    if (val0 != -9999 && val1 != -9999) {
        color0 = QColor(mCfg.ds.mColorMap.value(val0));
        color1 = QColor(mCfg.ds.mColorMap.value(val1));
    }

    QLinearGradient gradient;
    gradient.setStart(pix0);
    gradient.setFinalStop(pix1);
    gradient.setColorAt(0, color0);
    gradient.setColorAt(1, color1);

    // Painter
    QPainter p(&mImage);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QBrush(gradient), mCfg.mesh.mMeshBorderWidth));

    p.drawLine(pix0, pix1);
}

bool Renderer::nodeInsideView(uint nodeIndex)
{
    const Node& n = mMesh->projectedNode(nodeIndex);
    return pointInsideView(n.x, n.y);
}

bool Renderer::pointInsideView(double x, double y) {
    return x > mLlX && x < mUrX && y > mLlY && y < mUrY;
}

bool Renderer::elemOutsideView(uint i)
{
    const BBox& bbox = mMesh->projectedBBox(i);
    // Determine if this element is visible within the view
    return bbox.maxX < mLlX || bbox.minX > mUrX || bbox.minY > mUrY || bbox.maxY < mLlY;
}

QPoint Renderer::realToPixel(int nodeIndex)
{
    return realToPixelF(nodeIndex).toPoint();
}

QPointF Renderer::realToPixelF(int nodeIndex)
{
    const Node& n = mMesh->projectedNode(nodeIndex);
    return mtp.realToPixel(n.x, n.y);
}

void bbox2rect(const MapToPixel& mtp, const QSize& outputSize, const BBox& bbox, int& leftLim, int& rightLim, int& topLim, int& bottomLim)
{
    QPoint ll = mtp.realToPixel(bbox.minX, bbox.minY).toPoint();
    QPoint ur = mtp.realToPixel(bbox.maxX, bbox.maxY).toPoint();
    topLim = std::max( ur.y(), 0 );
    bottomLim = std::min( ll.y(), outputSize.height()-1 );
    leftLim = std::max( ll.x(), 0 );
    rightLim = std::min( ur.x(), outputSize.width()-1 );
}

void Renderer::bbox2rect(const BBox& bbox, int& leftLim, int& rightLim, int& topLim, int& bottomLim) {
    ::bbox2rect(mtp, mOutputSize, bbox, leftLim, rightLim, topLim, bottomLim);
}
