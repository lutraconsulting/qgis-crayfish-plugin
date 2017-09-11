#ifndef CRAYFISH_DATASET_UTILS_H
#define CRAYFISH_DATASET_UTILS_H

#include <QStringList>
#include <QMap>
#include <QVector>
#include <algorithm>
#include <functional>
#include <math.h>
#include <numeric>

#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

class CrayfishDataSetUtils
{
private:
  float fadd(float val1, float val2) const {return val1 + val2;}
  float fsubtract(float val1, float val2) const {return val1 - val2;}
  float fmultiply(float val1, float val2) const {return val1 * val2;}
  float fdivide(float val1, float val2) const {if (val2 == 0) return -9999; return val1 / val2;}
  float fpower(float val1, float val2) const {return pow(val1,val2);}
  float fequal(float val1, float val2) const {return val1 == val2;}
  float fnotEqual(float val1, float val2) const {return val1 != val2;}
  float fgreaterThan(float val1, float val2) const {return val1 > val2;}
  float flesserThan(float val1, float val2) const {return val1 < val2;}
  float flesserEqual(float val1, float val2) const {return val1 <= val2;}
  float flogicalAnd(float val1, float val2) const {return bool(val1) && bool(val2);}
  float flogicalOr(float val1, float val2) const {return bool(val1) || bool(val2);}
  float flogicalNot(float val1) const {return ! bool(val1);}
  float fchangeSign(float val1) const {return -val1;}
  float fmin(float val1, float val2) const {if (val1 > val2) {return val2;} else {return val1;}}
  float fmax(float val1, float val2) const {if (val1 < val2) {return val2;} else {return val1;}}
  float fabs(float val1) const {if (val1 > 0) {return val1;} else {return -val1;}}
  float fsum_aggr(QVector<float> vals) const {return std::accumulate(vals.begin(), vals.end(), 0.0);}
  float fmin_aggr(QVector<float> vals) const {return *std::min_element(vals.begin(), vals.end());}
  float fmax_aggr(QVector<float> vals) const {return *std::max_element(vals.begin(), vals.end());}
  float favg_aggr(QVector<float> vals) const {return fsum_aggr(vals) / vals.size();}

  Output* canditateOutput(DataSet &dataset, int time_index) const;
  const Output* constCanditateOutput(const DataSet& dataset, int time_index) const;
  int outputTimesCount(const DataSet& dataset1, const DataSet& dataset2) const;

  void func1(DataSet& dataset1, std::function<float(float)> func) const;
  void func2(DataSet& dataset1, const DataSet& dataset2, std::function<float(float,float)> func) const;
  void funcAggr(DataSet& dataset1, std::function<float(QVector<float>)> func) const;

  const Mesh* mMesh;
  bool mIsValid; // all used datasets (in datasetMap) do have outputs for same times.
                 // all used dataset names are present in mesh
  QVector<float> mTimes;
  QMap < QString, const DataSet* > mDatasetMap;

public:
    CrayfishDataSetUtils(const Mesh* mesh, const QStringList& usedDatasetNames);
    bool isValid();
    const Mesh* mesh() const { return mMesh; }
    const DataSet* dataset( const QString& datasetName ) const {const DataSet* ds = mDatasetMap[datasetName]; return ds;}

    // TODO FILTERS! 
    void ones( DataSet& dataset1) const;
    void nodata( DataSet& dataset1) const;
    void copy( DataSet& dataset1, const QString& datasetName ) const;
    void copy( DataSet& dataset1, const DataSet& dataset2 ) const;
    void number( DataSet& dataset1, float val) const;

    void logicalNot(DataSet& dataset1) const {return func1(dataset1, std::bind(&CrayfishDataSetUtils::flogicalNot, this, std::placeholders::_1));}
    void changeSign(DataSet& dataset1) const {return func1(dataset1, std::bind(&CrayfishDataSetUtils::fchangeSign, this, std::placeholders::_1));}
    void abs(DataSet& dataset1) const {return func1(dataset1, std::bind(&CrayfishDataSetUtils::fabs, this, std::placeholders::_1));}

    void add(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fadd, this, std::placeholders::_1, std::placeholders::_2));}
    void subtract(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fsubtract, this, std::placeholders::_1, std::placeholders::_2));}
    void multiply(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmultiply, this, std::placeholders::_1, std::placeholders::_2));}
    void divide(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fdivide, this, std::placeholders::_1, std::placeholders::_2));}
    void power(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fpower, this, std::placeholders::_1, std::placeholders::_2));}
    void equal(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fequal, this, std::placeholders::_1, std::placeholders::_2));}
    void notEqual(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fnotEqual, this, std::placeholders::_1, std::placeholders::_2));}
    void greaterThan(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fgreaterThan, this, std::placeholders::_1, std::placeholders::_2));}
    void lesserThan(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flesserThan, this, std::placeholders::_1, std::placeholders::_2));}
    void lesserEqual(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flesserEqual, this, std::placeholders::_1, std::placeholders::_2));}
    void logicalAnd(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flogicalAnd, this, std::placeholders::_1, std::placeholders::_2));}
    void logicalOr(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flogicalOr, this, std::placeholders::_1, std::placeholders::_2));}
    void min(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmin, this, std::placeholders::_1, std::placeholders::_2));}
    void max(DataSet& dataset1, const DataSet& dataset2) const {return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmax, this, std::placeholders::_1, std::placeholders::_2));}

    void sum_aggr(DataSet& dataset1) const {return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fsum_aggr, this, std::placeholders::_1));}
    void min_aggr(DataSet& dataset1) const {return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fmin_aggr, this, std::placeholders::_1));}
    void max_aggr(DataSet& dataset1) const {return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fmax_aggr, this, std::placeholders::_1));}
    void avg_aggr(DataSet& dataset1) const {return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::favg_aggr, this, std::placeholders::_1));}
};


#endif // CRAYFISH_DATASET_UTILS_H
