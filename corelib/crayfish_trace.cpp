#include <stdlib.h>     /* srand, rand */
#include <time.h>       /* time */
#include <climits>

#include "crayfish_trace.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_utils.h"
#include "crayfish_renderer.h"

uint qHash(const QPoint &key) {
    uint res = 0;
    res += key.x() * 10000;
    res += key.y();
    return res;
}


TraceRendererCache::TraceRendererCache()
  : mTraceIteration(0)
  , mCfg(0)
  , mtp(0)
{}

TraceRendererCache::~TraceRendererCache()
{
    if (mtp) delete mtp;
    if (mCfg) delete mCfg;
}

int TraceRendererCache::getNextIteration() {
    mTraceIteration = mTraceIteration + 1;
    if (mTraceIteration == INT_MAX - 1)
        mTraceIteration = 0;

    return mTraceIteration;
}

void TraceRendererCache::validateCache(const RendererConfig &cfg) {
    if (!isUpToDate(cfg)) {

        // set new input
        if (mCfg) delete mCfg;
        mCfg = new RendererConfig(cfg);
        if (mtp) delete mtp;
        mtp = new MapToPixel(cfg.llX, cfg.llY, cfg.pixelSize, cfg.outputSize.height());

        mUrX = mCfg->llX + (mCfg->outputSize.width()*mCfg->pixelSize);
        mUrY = mCfg->llY + (mCfg->outputSize.height()*mCfg->pixelSize);

        // delete old cache
        streamlines.clear();

        // refill the cache
        calculateStreamLines();
    }
}

bool TraceRendererCache::isUpToDate(const RendererConfig &cfg) const {
    // check only variables from config that we use in the cache
    return (mCfg &&
            (mCfg->outputMesh == cfg.outputMesh) &&
            (mCfg->outputVector == cfg.outputVector) &&
            (mCfg->outputSize == cfg.outputSize) &&
            (mCfg->ds.mVectorUserGrid == cfg.ds.mVectorUserGrid) &&
            equals(mCfg->llX, cfg.llX) &&
            equals(mCfg->llY, cfg.llY) &&
            equals(mCfg->pixelSize, cfg.pixelSize) &&
            (mCfg->ds.mVectorUserGridCellSize == cfg.ds.mVectorUserGridCellSize) &&
            equals(mCfg->ds.mVectorFilterMin, cfg.ds.mVectorFilterMin) &&
            equals(mCfg->ds.mVectorFilterMax, cfg.ds.mVectorFilterMax) &&
            equals(mCfg->ds.mScaleFactor, cfg.ds.mScaleFactor) &&
            equals(mCfg->ds.mVectorTraceCalculationSteps, cfg.ds.mVectorTraceCalculationSteps) &&
            (mCfg->ds.mVectorTraceParticles == cfg.ds.mVectorTraceParticles) &&
            (mCfg->ds.mVectorTraceParticlesCount == cfg.ds.mVectorTraceParticlesCount)
            );
}

bool TraceRendererCache::pointInsideView(const QPointF& pt) const {
    return pt.x() > mCfg->llX && pt.x() < mUrX && pt.y() > mCfg->llY && pt.y() < mUrY;
}

static double random01() {
    return ((double) rand() / (RAND_MAX));
}

QPointF TraceRendererCache::randomPoint() const {
    float x = random01() * (mUrX - mCfg->llX) + mCfg->llX;
    float y = random01() * (mUrY - mCfg->llY) + mCfg->llY;
    return QPointF(x, y);
}

QVector<QPointF> TraceRendererCache::calculateStartPoints() {
    // Calculate starting points for streamlines
    QVector<QPointF> startPoints;

    if (mCfg->ds.mVectorTraceParticles) {
        srand (time(NULL));
        for (int i=0; i<mCfg->ds.mVectorTraceParticlesCount; ++i)
            startPoints.append(randomPoint());
    } else if (mCfg->ds.mVectorUserGrid) {
        float x_plus = mCfg->ds.mVectorUserGridCellSize.width()*mCfg->pixelSize;
        float y_plus = mCfg->ds.mVectorUserGridCellSize.height()*mCfg->pixelSize;

        for (float x = mCfg->llX; x < mUrX; x += x_plus) {
            for (float y = mCfg->llY; y < mUrY; y += y_plus) {
                startPoints.append(QPointF(x, y));
            }
        }
    } else {
        for (int i = 0; i<mCfg->outputMesh->nodes().size(); i++) {
            QPointF pt(mCfg->outputMesh->nodes().at(i).toPointF());
            if (!pointInsideView(pt))
                continue;
            startPoints.append(pt);
        }
    }

    return startPoints;
}

ValuesCacheHash TraceRendererCache::calculateValuesCache() {
    // Calculate candidate element's
    BBox bbox(mCfg->llX, mUrX, mCfg->llY, mUrY);
    QSet<uint> candidateElementIds = mCfg->outputMesh->getCandidateElementIds(bbox);

    // Now calculate vector quantities for all pixels in range
    // key: x, y in pixels
    // value: vector_x, vector_y for pixel
    ValuesCacheHash values_cache;
    foreach (int i, candidateElementIds) {
        const BBox& elemBbox = mCfg->outputMesh->projectedBBox(i);

        // Get the BBox of the element in pixels
        int topLim, bottomLim, leftLim, rightLim;
        bbox2rect(*mtp, mCfg->outputSize, elemBbox, leftLim, rightLim, topLim, bottomLim);

        for(int y=topLim; y<=bottomLim; y++) {
            for(int x=leftLim; x<=rightLim; x++) {
                 QPointF val;
                 if (value(i, mtp->pixelToReal(x, y), val))
                    values_cache[QPoint(x, y)] = val;
            }
        }
    }
    return values_cache;
}

void TraceRendererCache::calculateStreamLines() {
    ValuesCacheHash values_cache = calculateValuesCache();

    QVector<QPointF> startPoints = calculateStartPoints();
    foreach (const QPointF& startPoint, startPoints) {
            QPointF pt(startPoint);
            TraceStreamLine streamline;

            for (int j=0; j<mCfg->ds.mVectorTraceCalculationSteps; ++j) {
                // get vector value at the point of interest from cache
                QPointF lineStart = mtp->realToPixel(pt);
                QPointF val;
                QHash<QPoint, QPointF>::const_iterator iter = values_cache.find(lineStart.toPoint());
                if (iter == values_cache.constEnd()) {
                    break; // not cached value
                } else {
                    val = iter.value();
                }

                // calculate line
                QPointF lineEnd;
                float vectorLength;
                double cosAlpha, sinAlpha;
                if (calcVectorLineEnd(lineEnd, vectorLength, cosAlpha, sinAlpha,
                                      mCfg, mCfg->outputVector, lineStart, val.x(), val.y()))
                    break;

                pt = mtp->pixelToReal(lineEnd);
                if (!pointInsideView(pt))
                    break;

                // OK we have another valid point, add it to the streamline
                if (j==0)
                    streamline.append(lineStart);
                streamline.append(lineEnd);
            }

            // add only non-empty streamlines
            if (streamline.size() > 1) {
                streamlines.append(streamline);
            }
        }
}

bool TraceRendererCache::value(uint elementIndex, const QPointF& pt, QPointF& val) const {
    double vx, vy;
    bool res = mCfg->outputMesh->vectorValueAt(elementIndex, pt.x(), pt.y(), &vx, &vy, mCfg->outputVector);
    if (res) {
        val.setX(vx);
        val.setY(vy);
    }

    return res && (vx != -9999) && (vy != -9999);
}

