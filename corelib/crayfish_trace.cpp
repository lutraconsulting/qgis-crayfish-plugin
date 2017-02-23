

#include "crayfish_trace.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_utils.h"
#include "crayfish_renderer.h"



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
    mTraceIteration = mTraceIteration % mCfg->ds.mVectorTraceAnimationSteps;
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
            equals(mCfg->ds.mVectorTraceCalculationSteps, cfg.ds.mVectorTraceCalculationSteps)
            );
}

bool TraceRendererCache::pointInsideView(const QPointF& pt) const {
    return pt.x() > mCfg->llX && pt.x() < mUrX && pt.y() > mCfg->llY && pt.y() < mUrY;
}

void TraceRendererCache::calculateStreamLines() {

    // Calculate starting points for streamlines
    QVector<QPointF> startPoints;

    if (mCfg->ds.mVectorUserGrid) {
        float x_plus = mCfg->ds.mVectorUserGridCellSize.width()*mCfg->pixelSize;
        float y_plus = mCfg->ds.mVectorUserGridCellSize.height()*mCfg->pixelSize;

        for (float x = mCfg->llX; x < mUrX; x += x_plus) {
            for (float y = mCfg->llY; y < mUrY; y += y_plus) {
                startPoints.append(QPointF(x, y));
            }
        }

    } else {
        for (int i = 0; i<mCfg->outputMesh->nodes().size(); i++)
            startPoints.append(mCfg->outputMesh->nodes().at(i).toPointF());
    }

    // Calculate candidate element's
    // TODO to be removed when spatial index is implemented
    BBox bbox;
    bbox.minX = mCfg->llX;
    bbox.maxX = mUrX;
    bbox.minY = mCfg->llY;
    bbox.maxY = mUrY;
    QSet<uint> candidateElementIds = mCfg->outputMesh->getCandidateElementIds(bbox);

    // now calculate all streamlines
    foreach (const QPointF& startPoint, startPoints) {
            QPointF pt(startPoint);

            if (!pointInsideView(pt))
                continue;

            TraceStreamLine streamline;

            for (int j=0; j<mCfg->ds.mVectorTraceCalculationSteps; ++j) {
                // calculate vector value at the point of interest
                QPointF val;
                if (!value(pt, val, candidateElementIds))
                    break;

                // calculate line
                QPointF lineStart = mtp->realToPixel(pt);
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

bool TraceRendererCache::value(const QPointF& pt, QPointF& val, const QSet<uint> &candidateElementIds) const {
    double vx, vy;
    bool res = mCfg->outputMesh->vectorValueAt(candidateElementIds, mCfg->outputVector, pt.x(), pt.y(), &vx, &vy);

    if (vx == -9999 || vy == -9999)
        return false;

    if (res) {
        val.setX(vx);
        val.setY(vy);
    }
    return res;
}

