#ifndef CRAYFISH_TRACE_H
#define CRAYFISH_TRACE_H

#include <QSize>
#include <QVector>
#include <QPointF>
#include <QPoint>
#include <QLineF>
#include <QHash>
#include <QSet>

class Output;
class MapToPixel;
struct RendererConfig;

typedef QVector<QPointF> TraceStreamLine;
typedef QHash<QPoint, QPointF> ValuesCacheHash;

class TraceRendererCache {
public:
    TraceRendererCache();
    ~TraceRendererCache();
    int getNextIteration();
    void validateCache(const RendererConfig& cfg);

    int getStreamLinesCount() {
        return streamlines.count();
    }

    const TraceStreamLine& getStreamLine(int i) {
        return streamlines.at(i);
    }

private:
    bool isUpToDate(const RendererConfig& cfg) const;
    QVector<QPointF> calculateStartPoints();
    void calculateStreamLines();
    ValuesCacheHash calculateValuesCache();
    bool pointInsideView(const QPointF& pt) const;
    bool value(uint elementIndex, const QPointF& pt, QPointF& res) const;
    QPointF randomPoint() const;

    //! iteration of trace rendering
    //! to simulate the "flow" animation on canvas
    //! we need to render different images
    //! based on some counter
    int mTraceIteration;

    //! rendering configuration
    RendererConfig* mCfg;

    //! cached values
    double mUrX;
    double mUrY;
    float vectorScaleFactor;
    MapToPixel* mtp;
    QVector<TraceStreamLine> streamlines;
};

#endif // CRAYFISH_TRACE_H
