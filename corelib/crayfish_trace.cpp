

#include "crayfish_trace.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_utils.h"
#include "crayfish_renderer.h"



TraceRendererCache::TraceRendererCache()
    : mCachedOutput(0)
    , mCachedLlX(0)
    , mCachedLlY(0)
    , mCachedUrX(0)
    , mCachedUrY(0)
    , mCachedPixelSize(0)
    , mCachedNRows(0)
    , mtp(0)
{
}

TraceRendererCache::~TraceRendererCache()
{
    if (mtp) delete mtp;
}

int TraceRendererCache::getNextIteration() {
    mTraceIteration = mTraceIteration % 5 + 1;
    return mTraceIteration;
}

void TraceRendererCache::validateCache(const Output* o, const Renderer *r) {


    if (!isUpToDate(o, r)) {

        // set new input
        mCachedOutput = o;

        mCachedLlX = r->mLlX;
        mCachedLlY = r->mLlY;
        mCachedUrX = r->mUrX;
        mCachedUrY = r->mUrY;
        mCachedPixelSize = r->mPixelSize;
        mCachedNRows = r->mOutputSize.height();
        mCachedGridCellSize = r->mCfg.ds.mVectorUserGridCellSize;
        mCachedMagnitudeMin = r->mCfg.ds.mVectorFilterMin;
        mCachedMagnitudeMax = r->mCfg.ds.mVectorFilterMax;
        mCachedScaleFactor = r->mCfg.ds.mScaleFactor;

        // delete old cache
        streamlines.clear();

        // refill the cache
        calculate();
    }


}


bool TraceRendererCache::isUpToDate(const Output* o, const Renderer *r) const {
    return ((o == mCachedOutput) &&
            equals(r->mLlX, mCachedLlX) &&
            equals(r->mLlY, mCachedLlY) &&
            equals(r->mUrX, mCachedUrX) &&
            equals(r->mUrY, mCachedUrY) &&
            equals(r->mPixelSize, mCachedPixelSize) &&
            equals(r->mOutputSize.height(), mCachedNRows) &&
            equals(r->mCfg.ds.mVectorUserGridCellSize.width(), mCachedGridCellSize.width()) &&
            equals(r->mCfg.ds.mVectorUserGridCellSize.height(), mCachedGridCellSize.height()) &&
            equals(r->mCfg.ds.mVectorFilterMin, mCachedMagnitudeMin) &&
            equals(r->mCfg.ds.mVectorFilterMax, mCachedMagnitudeMax) &&
            equals(r->mCfg.ds.mScaleFactor, mCachedScaleFactor));
}

bool TraceRendererCache::pointInsideView(const QPointF& pt) const {
    return pt.x() > mCachedLlX && pt.x() < mCachedUrX && pt.y() > mCachedLlY && pt.y() < mCachedUrY;
}

QPointF TraceRendererCache::randomPoint() const {
    float x = mCachedLlX + (mCachedUrX - mCachedLlX) * ((rand() % 10 + 1) / 10.0f);
    float y = mCachedLlY + (mCachedUrY - mCachedLlY) * ((rand() % 10 + 1) / 10.0f);
    return QPointF(x, y);
}

void TraceRendererCache::calculate() {

    if (mtp) delete mtp;
    mtp = new MapToPixel(mCachedLlX, mCachedLlY, mCachedPixelSize, mCachedNRows);

    mMaxIterationSteps = 150; //FIXME - to config

    const Mesh* mesh = mCachedOutput->dataSet->mesh();

    /* initialize random seed: */
    srand (time(NULL));

      for (float x = mCachedLlX; x < mCachedUrX; x += mCachedGridCellSize.width())
      {
        for (float y = mCachedLlY; y < mCachedUrY; y += mCachedGridCellSize.height())
        {
           QPointF pt(x, y);


    //for (int n=0; n<mNStreamLines; ++n) {
        //QPointF pt = randomPoint();

        TraceStreamLine streamline;

        for (int j=0; j<mMaxIterationSteps; ++j) {

            if (!pointInsideView(pt))
                break;

            TraceIterationStep step = calculateTraceIterationStep(pt);

            if (step.isEmpty())
                break;

            QPointF lineEnd = step.last().p2();
            streamline.append(step);

            pt = mtp->pixelToReal(lineEnd.x(), lineEnd.y());
        }

        if (!streamline.isEmpty()) {
            streamlines.append(streamline);
        }
    }}
}

bool TraceRendererCache::value(const QPointF& pt, QPointF& val) const {
    const Mesh* m = mCachedOutput->dataSet->mesh();
    double vx, vy;
    bool res = m->vectorValueAt(mCachedOutput, pt.x(), pt.y(), &vx, &vy);

    if (res) {
        val.setX(vx);
        val.setY(vy);
    }
    return res;
}

TraceIterationStep TraceRendererCache::calculateTraceIterationStep(QPointF pt) const {
    TraceIterationStep step;

    QPointF val;
    if (!value(pt, val))
        return step;

    float magnitude = val.manhattanLength();
    if (magnitude < mCachedMagnitudeMin || magnitude > mCachedMagnitudeMax)
        return step;

    QPointF lineStart = mtp->realToPixel(pt);
    float xDist = mCachedScaleFactor * val.x();
    float yDist = mCachedScaleFactor * val.y();
    // Flip the Y axis (pixel vs real-world axis)
    yDist *= -1.0;

    // Determine the line coords
    QPointF lineEnd(lineStart.x() + xDist,
                    lineStart.y() + yDist);

    QLineF line(lineStart, lineEnd);
    step.append(line);

    return step;
}
