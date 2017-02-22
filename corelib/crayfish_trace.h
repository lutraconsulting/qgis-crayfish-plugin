#ifndef CRAYFISH_TRACE_H
#define CRAYFISH_TRACE_H

#include <QSize>
#include <QVector>
#include <QPointF>
#include <QLineF>

class Output;
class MapToPixel;
class Renderer;

typedef QVector<QLineF> TraceIterationStep;
typedef QVector<TraceIterationStep> TraceStreamLine;

class TraceRendererCache {
public:
    TraceRendererCache();
    ~TraceRendererCache();
    int getNextIteration();
    void validateCache(const Output* o,
                       const Renderer* r);

    int getStreamLinesCount() {
        return streamlines.count();
    }

    const TraceStreamLine& getStreamLine(int i) {
        return streamlines.at(i);
    }

private:
    bool isUpToDate(const Output* o, const Renderer *r) const;
    void calculate();
    bool pointInsideView(const QPointF& pt) const;
    bool value(const QPointF& pt, QPointF &val) const;


    TraceIterationStep calculateTraceIterationStep(QPointF startPoint) const;


    QPointF randomPoint() const;

    int mTraceIteration; //!< iteration of trace rendering
    int mNStreamLines; //!< number of streamlines
    int mMaxIterationSteps; //!< maximum number of iterations
    const Output* mCachedOutput; //!< vector output
    double mCachedLlX; //!< X of current view's lower-left point (mesh coords)
    double mCachedLlY; //!< Y of current view's lower-left point (mesh coords)
    double mCachedUrX; //!< X of current view's upper-right point (mesh coords)
    double mCachedUrY; //!< Y of current view's upper-right point (mesh coords)
    double mCachedPixelSize;
    int mCachedNRows;
    QSize mCachedGridCellSize;
    float mCachedMagnitudeMin;
    float mCachedMagnitudeMax;
    float mCachedScaleFactor;

    MapToPixel* mtp;
    QVector<TraceStreamLine> streamlines;
};

#endif // CRAYFISH_TRACE_H
