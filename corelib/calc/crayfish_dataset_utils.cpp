#include "calc/crayfish_dataset_utils.h"
#include "crayfish_utils.h"
#include "geos_c.h"

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}

const float F_TRUE = 1.0f;
const float F_FALSE = 0.0f;
const float F_NODATA = -9999.0f;

CrayfishDataSetUtils::CrayfishDataSetUtils(const Mesh *mesh, const QStringList& usedDatasetNames, float startTime, float endTime)
    : mMesh(mesh)
    , mIsValid(false)
    , mOutputType(Output::TypeNode) // right now we support only NodeOutputs
{
    // First populate datasetMap and see if we have all datasets present
    foreach (const QString& datasetName, usedDatasetNames )
    {
        DataSet* ds = mMesh->dataSet(datasetName);
        if (ds == 0)
            return;

        mDatasetMap.insert(datasetName, ds);
    }

    // Now populate used times and check that all datasets do have some times
    // OR just one time (== one output)
    bool times_populated = false;
    foreach (const DataSet* ds, mDatasetMap.values()) {
        if (ds->outputCount() == 0) {
            // dataset must have at least 1 output
            return;
        }

        if (ds->outputCount() > 1) {

            if (times_populated)
            {
                if (ds->outputCount() != mTimes.size()) {
                    // different number of outputs in the datasets
                    return;
                }
            }

            for(int output_index=0; output_index < ds->outputCount(); ++output_index) {
                const Output* o = ds->constOutput(output_index);
                if (times_populated) {
                    if ( fabs(mTimes[output_index] - o->time) > 1e-5 )
                    {
                        // error, the times in different datasets differs
                        return;
                    }
                } else {
                    mTimes.append(o->time);
                }
            }

            times_populated = true;
        }
    }

    // case of all datasets not time varying of usedDatasetNames is empty
    if (mTimes.isEmpty()) {
        mTimes.push_back(0.0f);
    } else {
        // filter out times we do not need to speed up calculations
        for (QVector<float>::iterator it=mTimes.begin();it!=mTimes.end();)
        {
           if (equals(*it, startTime) ||
               equals(*it, endTime) ||
               ((*it >= startTime) && (*it <= endTime)))
                   ++it;
           else
                   it = mTimes.erase(it);
        }
    }

    // check that all outputs are of the same type
    // right now we support only NodeOutputs,
    // because also SMS .dat files support only NodeOutputs
    foreach (const DataSet* ds, mDatasetMap.values()) {
        for(int output_index=0; output_index < ds->outputCount(); ++output_index) {
            const Output* o = ds->constOutput(output_index);
            if (o->type() != mOutputType)
                return;
        }
    }

    // All is valid!
    mIsValid = true;
}

bool CrayfishDataSetUtils::isValid() const
{
    return mIsValid;
}

void CrayfishDataSetUtils::populateSpatialFilter(DataSet& filter, const BBox& outputExtent) const
{
    filter.deleteOutputs();
    if (mOutputType == Output::TypeNode) {
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                     mMesh->elements().size(),
                     DataSet::Scalar);
        output->time = mTimes[0];
        for (int i = 0; i < mMesh->nodes().size(); ++i)
        {
            QPointF point = mMesh->projectedNode(i).toPointF();
            if (outputExtent.isPointInside(point)) {
                output->getValues()[i] = F_TRUE;
            } else {
                output->getValues()[i] = F_FALSE;
            }
        }
        memset(output->getActive().data(), 1, mMesh->elements().size());
        filter.addOutput(output);
    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = mTimes[0];
        for (int i = 0; i < mMesh->elements().size(); ++i) {
            const BBox& box = mMesh->projectedBBox(i);
            if (outputExtent.contains(box)) {
                output->getValues()[i] = F_TRUE;
            } else {
                output->getValues()[i] = F_FALSE;
            }
        }
        filter.addOutput(output);
    }
}

void geosNoticeFunc(const char *message, ...)
{
    printf("Notification from GEOS lib: %s\n", message);
}

void geosErrorFunc(const char *message, ...)
{
    printf("An Error occured in GEOS lib: %s\n", message);
}

void CrayfishDataSetUtils::populateMaskFilter(DataSet& filter, const char* maskWkt) const
{
    filter.deleteOutputs();
    GEOSGeometry* maskGeom;
    GEOSContextHandle_t cx = GEOS_init_r();
    GEOSContext_setNoticeHandler_r(cx, &geosNoticeFunc);
    GEOSContext_setErrorHandler_r(cx, &geosErrorFunc);

    GEOSWKTReader *reader = GEOSWKTReader_create_r(cx);
    maskGeom = GEOSWKTReader_read_r(cx, reader, maskWkt);

    if (mOutputType == Output::TypeNode) {
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                     mMesh->elements().size(),
                     DataSet::Scalar);
        output->time = mTimes[0];
        for (int i = 0; i < mMesh->nodes().size(); ++i)
        {
            const char* pointWkt = mMesh->projectedNode(i).toWkt().toLatin1().data();
            GEOSGeometry* pointGeom;
            pointGeom = GEOSWKTReader_read_r(cx, reader, pointWkt);

            char a = GEOSIntersects_r(cx, maskGeom, pointGeom);
              if (a == 1) {
                  output->getValues()[i] = F_TRUE;
              } else {
                  output->getValues()[i] = F_FALSE;
              }
              GEOSGeom_destroy_r(cx, pointGeom);
        }
        memset(output->getActive().data(), 1, mMesh->elements().size());
        filter.addOutput(output);
    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = mTimes[0];
        for (int i = 0; i < mMesh->elements().size(); ++i) {
            const char* bbox = mMesh->projectedBBox(i).toWkt().toLatin1().data();;
            GEOSGeometry* pointBBoxGeom = GEOSWKTReader_read_r(cx, reader, bbox);

            char a = GEOSIntersects_r(cx, maskGeom, pointBBoxGeom);
            if (a == 1) {
                output->getValues()[i] = F_TRUE;
            } else {
                output->getValues()[i] = F_FALSE;
            }
            GEOSGeom_destroy_r(cx, pointBBoxGeom);
        }
        filter.addOutput(output);
    }
    GEOSWKTReader_destroy_r(cx, reader);
    GEOS_finish_r(cx);
}

Output* CrayfishDataSetUtils::number(float val, float time) const {
    Q_ASSERT(isValid());

    if (mOutputType == Output::TypeNode) {
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                mMesh->elements().size(),
                DataSet::Scalar);
        output->time = time;

        memset(output->getActive().data(), !is_nodata(val), mMesh->elements().size());
        for (int i = 0; i < mMesh->nodes().size(); ++i) // Using for loop we are initializing
        {
            output->getValues()[i] = val;
        }
        return output;
    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = time;

        for (int i = 0; i < mMesh->elements().size(); ++i) // Using for loop we are initializing
        {
            output->getValues()[i] = val;
        }
        return output;
    }
}

void CrayfishDataSetUtils::number(DataSet& dataset1, float val) const
{
    Q_ASSERT(isValid());

    dataset1.deleteOutputs();
    Output * output = number(val, mTimes[0]);
    dataset1.addOutput(output);
}


void CrayfishDataSetUtils::ones(DataSet& dataset1) const {
    Q_ASSERT(isValid());

    number(dataset1, 1.0f);
}

void CrayfishDataSetUtils::nodata(DataSet& dataset1) const {
    Q_ASSERT(isValid());

    number(dataset1, F_NODATA);
}


Output* CrayfishDataSetUtils::copy(const Output* o0 ) const {
    Q_ASSERT(isValid());
    Q_ASSERT(o0 != 0);

    if (o0->type() == Output::TypeNode) {
        const NodeOutput* node_o0 = static_cast<const NodeOutput*>(o0);

        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                     mMesh->elements().size(),
                     DataSet::Scalar);
        output->time = node_o0->time;

        for (int n=0; n<mMesh->nodes().size(); ++n)
            output->getValues()[n] = node_o0->loadedValues()[n];

        for (int n=0; n<mMesh->elements().size(); ++n)
            output->getActive()[n] = node_o0->loadedActive()[n];

        return output;

    } else {
        const ElementOutput* elem_o0 = static_cast<const ElementOutput*>(o0);

        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = elem_o0->time;

        for (int n=0; n<mMesh->elements().size(); ++n)
        {
            output->getValues()[n] = elem_o0->loadedValues()[n];
        }

        return output;
    }

}

void CrayfishDataSetUtils::copy(DataSet& dataset1, const QString& datasetName) const {
    Q_ASSERT(isValid());

    const DataSet* dataset2 = dataset(datasetName);
    Q_ASSERT(dataset2 != 0);

    if (dataset2->outputCount() == 1) {
        // Always copy
        const Output* o0 = dataset2->constOutput(0);
        Output* output = copy(o0);
        dataset1.addOutput(output);
    } else {
        for(int output_index=0; output_index < dataset2->outputCount(); ++output_index) {
            const Output* o0 = dataset2->constOutput(output_index);
            if (equals(o0->time, mTimes.first()) ||
                equals(o0->time, mTimes.last()) ||
                ((o0->time >= mTimes.first()) && (o0->time <= mTimes.last()))
               )
            {
                Output* output = copy(o0);
                dataset1.addOutput(output);
            }
        }
    }
}

void CrayfishDataSetUtils::tranferOutputs( DataSet& dataset1, DataSet& dataset2 ) const {
    Q_ASSERT(isValid());

    dataset1.deleteOutputs();
    for (int i=0; i<dataset2.outputCount(); ++i) {
        Output* o = dataset2.output(i);
        Q_ASSERT(o != 0);
        dataset1.addOutput(o);
    }
    dataset2.dispatchOutputs();
}

void CrayfishDataSetUtils::expand( DataSet& dataset1, const DataSet& dataset2 ) const {
    Q_ASSERT(isValid());

    if (dataset2.outputCount() > 1) {
        if (dataset1.outputCount() == 1) {
            const Output* o0 = dataset1.output(0);
            Q_ASSERT(o0 != 0);
            for (int i=1; i<dataset2.outputCount(); ++i) {
                Output* o = copy(o0);
                o->time = mTimes[i];
                dataset1.addOutput(o);
            }
        }
    }
}


Output* CrayfishDataSetUtils::canditateOutput(DataSet& dataset, int time_index) const {
    Q_ASSERT(isValid());

    if (dataset.outputCount() > 1) {
        Q_ASSERT(dataset.outputCount() > time_index);
        return dataset.output(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.output(0);
    }
}

const Output* CrayfishDataSetUtils::constCanditateOutput(const DataSet& dataset, int time_index) const {
    Q_ASSERT(isValid());

    if (dataset.outputCount() > 1) {
        Q_ASSERT(dataset.outputCount() > time_index);
        return dataset.constOutput(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.constOutput(0);
    }
}

int CrayfishDataSetUtils::outputTimesCount(const DataSet& dataset1, const DataSet& dataset2) const {
    Q_ASSERT(isValid());

    if ( (dataset1.outputCount() > 1) || ( dataset2.outputCount() > 1 )) {
        return mTimes.size();
    } else {
        return 1;
    }
}

void CrayfishDataSetUtils::func1(DataSet& dataset1, std::function<float(float)> func) const {
    Q_ASSERT(isValid());

    for (int time_index=0; time_index<dataset1.outputCount(); ++time_index) {
        Output* output = canditateOutput(dataset1, time_index);
        if (output->type() == Output::TypeNode ) {
            NodeOutput* nodeOutput = static_cast<NodeOutput*>(output);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, nodeOutput);
                float res_val = F_NODATA;
                if (!is_nodata(val1))
                    res_val = func(val1);
                nodeOutput->getValues()[n] = res_val;
            }

            activate(nodeOutput);

        } else {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(output);
            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, elemOutput);               
                float res_val = F_NODATA;
                if (!is_nodata(val1))
                    res_val = func(val1);
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}


void CrayfishDataSetUtils::func2(DataSet& dataset1, const DataSet& dataset2, std::function<float(float,float)> func) const {
    Q_ASSERT(isValid());

    expand(dataset1, dataset2);

    for (int time_index=0; time_index<outputTimesCount(dataset1, dataset2); ++time_index) {
        Output* o1 = canditateOutput(dataset1, time_index);
        const Output* o2 = constCanditateOutput(dataset2, time_index);

        Q_ASSERT(o1->type() == o2->type()); // we do not support mixed output types

        if (o1->type() == Output::TypeNode ) {

            NodeOutput* nodeOutput = static_cast<NodeOutput*>(o1);
            const NodeOutput* nodeOutput2 = static_cast<const NodeOutput*>(o2);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, o1);
                float val2 = mMesh->valueAt(n, o2);
                float res_val = F_NODATA;
                if (!is_nodata(val1) && !is_nodata(val2))
                    res_val = func(val1, val2);
                nodeOutput->getValues()[n] = res_val;
            }

            activate(nodeOutput, nodeOutput2);

        } else // o1->type() == Output::TypeElement
        {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(o1);

            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, o1);
                float val2 = mMesh->valueAt(n, o2);
                float res_val = F_NODATA;
                if (!is_nodata(val1) && !is_nodata(val2))
                    res_val = func(val1, val2);
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}

void CrayfishDataSetUtils::funcAggr(DataSet& dataset1, std::function<float(QVector<float>&)> func) const {
    Q_ASSERT(isValid());

    Output* o0 = canditateOutput(dataset1, 0);

    if (o0->type() == Output::TypeNode ) {
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                mMesh->elements().size(),
                DataSet::Scalar);
        output->time = mTimes[0];
        for (int n=0; n<mMesh->nodes().size(); ++n)
        {
            QVector < float > vals;
            for (int time_index=0; time_index<dataset1.outputCount(); ++time_index) {
                const Output* o1 = canditateOutput(dataset1, time_index);
                Q_ASSERT(o1->type() == o0->type());
                float val1 = mMesh->valueAt(n, o1);
                // ideally we should take only values from cells that are active.
                // but the problem is that the node can be part of multiple cells,
                // few active and few not, ...
                if (!is_nodata(val1)) {
                    vals.push_back(val1);
                }
            }

            float res_val = F_NODATA;
            if (!vals.isEmpty()) {
                res_val = func(vals);
            }

            output->getValues()[n] = res_val;
        }

        // lets do activation purely on NODATA values as we did aggregation here
        memset(output->getActive().data(), 1, mMesh->elements().size());
        activate(output);

        dataset1.deleteOutputs();
        dataset1.addOutput(output);

    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = mTimes[0];

        for (int n=0; n<mMesh->elements().size(); ++n)
        {
            QVector < float > vals;
            for (int time_index=0; time_index<dataset1.outputCount(); ++time_index) {
                const Output* o1 = canditateOutput(dataset1, time_index);
                Q_ASSERT(o1->type() == o0->type());
                float val1 = mMesh->valueAt(n, o1);
                if (!is_nodata(val1)) {
                    vals.push_back(val1);
                }
            }

            float res_val = F_NODATA;
            if (!vals.isEmpty()) {
                res_val = func(vals);
            }

            output->getValues()[n] = res_val;
        }

        dataset1.deleteOutputs();
        dataset1.addOutput(output);
    }
}

void CrayfishDataSetUtils::add_if( DataSet& true_dataset,
                                   const DataSet& false_dataset,
                                   const DataSet& condition) const
{
    Q_ASSERT(isValid());

    // Make sure we have enough outputs in the resulting dataset
    expand(true_dataset, condition);
    expand(true_dataset, false_dataset);

    for (int time_index=0; time_index<true_dataset.outputCount(); ++time_index) {
        Output* true_o = canditateOutput(true_dataset, time_index);
        const Output* false_o = constCanditateOutput(false_dataset, time_index);
        const Output* condition_o = constCanditateOutput(condition, time_index);


        Q_ASSERT(true_o->type() == false_o->type()); // we do not support mixed output types
        Q_ASSERT(true_o->type() == condition_o->type()); // we do not support mixed output types

        if (true_o->type() == Output::TypeNode ) {

            NodeOutput* nodeOutput = static_cast<NodeOutput*>(true_o);
            const NodeOutput* nodeConditionOutput = static_cast<const NodeOutput*>(condition_o);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                float cond_val = mMesh->valueAt(n, condition_o);
                float res_val = F_NODATA;
                if (!is_nodata(cond_val)) {
                    if (equals(cond_val, F_TRUE))
                        res_val = mMesh->valueAt(n, true_o);
                    else
                        res_val = mMesh->valueAt(n, false_o);
                }
                nodeOutput->getValues()[n] = res_val;
            }

            // This is not ideal, as we do not check for true/false branch here in activate
            // problem is that activate is on elements, but condition is on nodes...
            memset(nodeOutput->getActive().data(), 1, mMesh->elements().size());
            activate(nodeOutput, nodeConditionOutput);

        } else // o1->type() == Output::TypeElement
        {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(true_o);

            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float cond_val = mMesh->valueAt(n, condition_o);
                float res_val = F_NODATA;
                if (!is_nodata(cond_val)) {
                    if (equals(cond_val, F_TRUE))
                        res_val = mMesh->valueAt(n, true_o);
                    else
                        res_val = mMesh->valueAt(n, false_o);
                }
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}


void CrayfishDataSetUtils::activate(DataSet& dataset1) const
{
    Q_ASSERT(isValid());

    if (mOutputType == Output::TypeNode) {
        for (int time_index=0; time_index<dataset1.outputCount(); ++time_index) {
            Output* o1 = canditateOutput(dataset1, time_index);
            Q_ASSERT(o1->type() == Output::TypeNode);
            NodeOutput* nodeOutput = static_cast<NodeOutput*>(o1);
            activate(nodeOutput);
        }
    }
    // Element outputs do not have activate array
}

void CrayfishDataSetUtils::activate(NodeOutput* tos, const NodeOutput *ref_output /*=0*/) const
{

    Q_ASSERT(isValid());
    Q_ASSERT(tos != 0);

    // Activate only elements that do all node's outputs with some data
    // And are not deactivated from the beginning
    for (int idx=0; idx<mMesh->elements().size(); ++idx)
    {
        if (ref_output != 0 && (!ref_output->loadedActive()[idx])) {
            tos->getActive()[idx] = false;
            continue;
        }

        if (!tos->getActive()[idx]) {
            continue;
        }

        Element elem = mMesh->elements().at(idx);

        bool is_active = true; //ACTIVE
        for (int j=0; j<elem.nodeCount(); ++j)
        {
            if (is_nodata(tos->getValues()[elem.p(0)])) {
                is_active = false; //NOT ACTIVE
                break;
            }
        }
        tos->getActive()[idx] = is_active;
    }
}

float CrayfishDataSetUtils::ffilter(float val1, float filter) const {
    Q_ASSERT(!is_nodata(val1));

    if (equals(filter, F_TRUE))
        return val1;
    else
        return F_NODATA;
}

float CrayfishDataSetUtils::fadd(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    return val1 + val2;

}

float CrayfishDataSetUtils::fsubtract(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    return val1 - val2;

}

float CrayfishDataSetUtils::fmultiply(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    return val1 * val2;

}

float CrayfishDataSetUtils::fdivide(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (equals(val2, 0.0f))
        return F_NODATA;
    else
        return val1 / val2;

}

float CrayfishDataSetUtils::fpower(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    return pow(val1, val2);

}

float CrayfishDataSetUtils::fequal(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (equals(val1, val2)) {
        return F_TRUE;
    } else {
        return F_FALSE;
    }

}

float CrayfishDataSetUtils::fnotEqual(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (equals(val1, val2)) {
        return F_FALSE;
    } else {
        return F_TRUE;
    }

}

float CrayfishDataSetUtils::fgreaterThan(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (val1 > val2) {
        return F_TRUE;
    } else {
        return F_FALSE;
    }

}

float CrayfishDataSetUtils::flesserThan(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (val1 < val2) {
        return F_TRUE;
    } else {
        return F_FALSE;
    }

}

float CrayfishDataSetUtils::flesserEqual(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (val1 <= val2) {
        return F_TRUE;
    } else {
        return F_FALSE;
    }

}

float CrayfishDataSetUtils::fgreaterEqual(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    if (val1 >= val2) {
        return F_TRUE;
    } else {
        return F_FALSE;
    }

}


float CrayfishDataSetUtils::flogicalAnd(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    bool bval1 = equals(val1, F_TRUE);
    bool bval2 = equals(val2, F_TRUE);
    if (bval1 && bval2)
        return F_TRUE;
    else
        return F_FALSE;

}

float CrayfishDataSetUtils::flogicalOr(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));
    bool bval1 = equals(val1, F_TRUE);
    bool bval2 = equals(val2, F_TRUE);
    if (bval1 || bval2)
        return F_TRUE;
    else
        return F_FALSE;

}

float CrayfishDataSetUtils::flogicalNot(float val1) const {
    Q_ASSERT(!is_nodata(val1));
    bool bval1 = equals(val1, F_TRUE);
    if (bval1)
        return F_FALSE;
    else
        return F_TRUE;

}

float CrayfishDataSetUtils::fchangeSign(float val1) const {
    Q_ASSERT(!is_nodata(val1));
    return -val1;
}

float CrayfishDataSetUtils::fmin(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    if (val1 > val2) {
        return val2;
    } else {
        return val1;
    }

}


float CrayfishDataSetUtils::fmax(float val1, float val2) const {
    Q_ASSERT(!is_nodata(val1));
    Q_ASSERT(!is_nodata(val2));


    if (val1 < val2) {
        return val2;
    } else {
        return val1;
    }

}

float CrayfishDataSetUtils::fabs(float val1) const {
    Q_ASSERT(!is_nodata(val1));


    if (val1 > 0) {
        return val1;
    } else {
        return -val1;
    }

}

float CrayfishDataSetUtils::fsum_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(F_NODATA));
    Q_ASSERT(!vals.isEmpty());
    return std::accumulate(vals.begin(), vals.end(), 0.0);
}

float CrayfishDataSetUtils::fmin_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(F_NODATA));
    Q_ASSERT(!vals.isEmpty());
    return *std::min_element(vals.begin(), vals.end());
}

float CrayfishDataSetUtils::fmax_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(F_NODATA));
    Q_ASSERT(!vals.isEmpty());
    return *std::max_element(vals.begin(), vals.end());
}

float CrayfishDataSetUtils::favg_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(F_NODATA));
    Q_ASSERT(!vals.isEmpty());
    return fsum_aggr(vals) / vals.size();
}

void CrayfishDataSetUtils::logicalNot(DataSet &dataset1) const {
    return func1(dataset1, std::bind(&CrayfishDataSetUtils::flogicalNot, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::changeSign(DataSet &dataset1) const {
    return func1(dataset1, std::bind(&CrayfishDataSetUtils::fchangeSign, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::abs(DataSet &dataset1) const {
    return func1(dataset1, std::bind(&CrayfishDataSetUtils::fabs, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::add(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fadd, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::subtract(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fsubtract, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::multiply(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmultiply, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::divide(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fdivide, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::power(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fpower, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::equal(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fequal, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::notEqual(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fnotEqual, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::greaterThan(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fgreaterThan, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::lesserThan(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flesserThan, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::lesserEqual(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flesserEqual, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::greaterEqual(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fgreaterEqual, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::logicalAnd(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flogicalAnd, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::logicalOr(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::flogicalOr, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::min(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmin, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::max(DataSet &dataset1, const DataSet &dataset2) const {
    return func2(dataset1, dataset2, std::bind(&CrayfishDataSetUtils::fmax, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::filter(DataSet &dataset1, const BBox &outputExtent) const {
    DataSet filter("filter");
    populateSpatialFilter(filter, outputExtent);
    return func2(dataset1, filter, std::bind(&CrayfishDataSetUtils::ffilter, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::filter(DataSet &dataset1, const char* maskWkt) const {
    DataSet filter("filter");
    populateMaskFilter(filter, maskWkt);
    return func2(dataset1, filter, std::bind(&CrayfishDataSetUtils::ffilter, this, std::placeholders::_1, std::placeholders::_2));
}

void CrayfishDataSetUtils::sum_aggr(DataSet &dataset1) const {
    return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fsum_aggr, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::min_aggr(DataSet &dataset1) const {
    return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fmin_aggr, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::max_aggr(DataSet &dataset1) const {
    return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::fmax_aggr, this, std::placeholders::_1));
}

void CrayfishDataSetUtils::avg_aggr(DataSet &dataset1) const {
    return funcAggr(dataset1, std::bind(&CrayfishDataSetUtils::favg_aggr, this, std::placeholders::_1));
}
