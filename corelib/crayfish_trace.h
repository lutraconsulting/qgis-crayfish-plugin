#ifndef CRAYFISH_TRACE_H
#define CRAYFISH_TRACE_H

#include <QSize>
#include <QVector>
#include <QPointF>
#include <QLineF>

class Output;
class MapToPixel;
struct RendererConfig;

typedef QVector<QPointF> TraceStreamLine;

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
    void calculateStreamLines();
    bool pointInsideView(const QPointF& pt) const;
    bool value(const QPointF& pt, QPointF &val, const QSet<uint>& candidateElementIds) const;

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
