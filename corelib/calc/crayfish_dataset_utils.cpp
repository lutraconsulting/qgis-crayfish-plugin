#include "calc/crayfish_dataset_utils.h"
#include "crayfish_utils.h"

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}

const float F_TRUE = 1.0f;
const float F_FALSE = 0.0f;


CrayfishDataSetUtils::CrayfishDataSetUtils(const Mesh *mesh, const QStringList& usedDatasetNames)
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

bool CrayfishDataSetUtils::isValid()
{
    return mIsValid;
}

void CrayfishDataSetUtils::number(DataSet& dataset1, float val) const
{
    dataset1.deleteOutputs();
    if (mOutputType == Output::TypeNode) {
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                mMesh->elements().size(),
                DataSet::Scalar);
        output->time = mTimes[0];

        memset(output->getActive().data(), !is_nodata(val), mMesh->elements().size());
        for (int i = 0; i < mMesh->nodes().size(); ++i) // Using for loop we are initializing
        {
            output->getValues()[i] = val;
        }
        dataset1.addOutput(output);
    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
        output->time = mTimes[0];

        for (int i = 0; i < mMesh->elements().size(); ++i) // Using for loop we are initializing
        {
            output->getValues()[i] = val;
        }
        dataset1.addOutput(output);
    }
}


void CrayfishDataSetUtils::ones(DataSet& dataset1) const {
    number(dataset1, 1.0f);
}

void CrayfishDataSetUtils::nodata(DataSet& dataset1) const {
    number(dataset1, -9999.0f);
}


Output* CrayfishDataSetUtils::copy(const Output* o0 ) const {
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

void CrayfishDataSetUtils::copy( DataSet& dataset1, const DataSet& dataset2 ) const {
    dataset1.deleteOutputs();

    for(int output_index=0; output_index < dataset2.outputCount(); ++output_index) {
        const Output* o0 = dataset2.constOutput(output_index);
        Output* output = copy(o0);
        dataset1.addOutput(output);
    }
}


void CrayfishDataSetUtils::copy(DataSet& dataset1, const QString& datasetName) const {
    const DataSet* ds0 = dataset(datasetName);
    Q_ASSERT(ds0 != 0);
    copy(dataset1, *ds0);
}


void CrayfishDataSetUtils::tranferOutputs( DataSet& dataset1, DataSet& dataset2 ) const {
    dataset1.deleteOutputs();
    for (int i=0; i<dataset2.outputCount(); ++i) {
        Output* o = dataset2.output(i);
        Q_ASSERT(o != 0);
        dataset1.addOutput(o);
    }
    dataset2.dispatchOutputs();
}

void CrayfishDataSetUtils::expand( DataSet& dataset1, const DataSet& dataset2 ) const {
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
    if (dataset.outputCount() > 1) {
        Q_ASSERT(dataset.outputCount() > time_index);
        return dataset.output(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.output(0);
    }
}

const Output* CrayfishDataSetUtils::constCanditateOutput(const DataSet& dataset, int time_index) const {
    if (dataset.outputCount() > 1) {
        Q_ASSERT(dataset.outputCount() > time_index);
        return dataset.constOutput(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.constOutput(0);
    }
}

int CrayfishDataSetUtils::outputTimesCount(const DataSet& dataset1, const DataSet& dataset2) const {
    if ( (dataset1.outputCount() > 1) || ( dataset2.outputCount() > 1 )) {
        return mTimes.size();
    } else {
        return 1;
    }
}

void CrayfishDataSetUtils::func1(DataSet& dataset1, std::function<float(float)> func) const {
    for (int time_index=0; time_index<dataset1.outputCount(); ++time_index) {
        Output* output = canditateOutput(dataset1, time_index);
        if (output->type() == Output::TypeNode ) {
            NodeOutput* nodeOutput = static_cast<NodeOutput*>(output);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, nodeOutput);
                float res = func(val1);
                nodeOutput->getValues()[n] = res;
            }

            activate(nodeOutput);

        } else {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(output);
            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, elemOutput);
                float res_val = func(val1);
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}


void CrayfishDataSetUtils::func2(DataSet& dataset1, const DataSet& dataset2, std::function<float(float,float)> func) const {

    expand(dataset1, dataset2);

    for (int time_index=0; time_index<outputTimesCount(dataset1, dataset2); ++time_index) {
        Output* o1 = canditateOutput(dataset1, time_index);
        const Output* o2 = constCanditateOutput(dataset2, time_index);

        Q_ASSERT(o1->type() == o2->type()); // we do not support mixed output types

        if (o1->type() == Output::TypeNode ) {

            NodeOutput* nodeOutput = static_cast<NodeOutput*>(o1);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, o1);
                float val2 = mMesh->valueAt(n, o2);
                float res_val = func(val1, val2);
                nodeOutput->getValues()[n] = res_val;
            }

            activate(nodeOutput);

        } else // o1->type() == Output::TypeElement
        {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(o1);

            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, o1);
                float val2 = mMesh->valueAt(n, o2);
                float res_val = func(val1, val2);
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}

void CrayfishDataSetUtils::funcAggr(DataSet& dataset1, std::function<float(QVector<float>&)> func) const {
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
                if (!is_nodata(val1)) {
                    vals.push_back(val1);
                }
            }

            float res_val = -9999;
            if (!vals.isEmpty()) {
                res_val = func(vals);
            }

            output->getValues()[n] = res_val;
        }

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
                if (val1 != -9999) {
                    vals.push_back(val1);
                }
            }

            float res_val = -9999;
            if (!vals.isEmpty()) {
                res_val = func(vals);
            }

            output->getValues()[n] = res_val;
        }

        dataset1.deleteOutputs();
        dataset1.addOutput(output);
    }
}

void CrayfishDataSetUtils::activate(DataSet& dataset1) const
{
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

void CrayfishDataSetUtils::activate(NodeOutput* tos) const
{
       // Activate only elements that do all node's outputs with some data
       for (int idx=0; idx<mMesh->elements().size(); ++idx)
       {
           Element elem = mMesh->elements().at(idx);

           bool is_active = true; //ACTIVE

           for (int j=0; j<elem.nodeCount(); ++j)
           {
               if (is_nodata(tos->getValues()[elem.p(0)]))
                   is_active = false; //NOT ACTIVE
               break;
           }

           tos->getActive()[idx] = is_active;
       }
}

float CrayfishDataSetUtils::ffilter(float val1, float filter) const {
    if (is_nodata(filter) || equals(filter, F_FALSE))
        return -9999.0f;
    else
        return val1;
}

float CrayfishDataSetUtils::fadd(float val1, float val2) const {
    if (is_nodata(val1)) {
        if (is_nodata(val2)) {
            return -9999.0f;
        } else {
            return val2;
        }
    } else {
        if (is_nodata(val2)) {
            return val1;
        } else {
            return val1 + val2;
        }
    }
}

float CrayfishDataSetUtils::fsubtract(float val1, float val2) const {
    if (is_nodata(val1)) {
        if (is_nodata(val2)) {
            return -9999.0f;
        } else {
            return val2;
        }
    } else {
        if (is_nodata(val2)) {
            return val1;
        } else {
            return val1 - val2;
        }
    }
}

float CrayfishDataSetUtils::fmultiply(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        return val1 * val2;
    }
}

float CrayfishDataSetUtils::fdivide(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (equals(val2, 0.0f))
            return -9999;
        else
            return val1 / val2;
    }
}

float CrayfishDataSetUtils::fpower(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        return pow(val1, val2);
    }
}

float CrayfishDataSetUtils::fequal(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (equals(val1, val2)) {
            return F_TRUE;
        } else {
            return F_FALSE;
        }
    }
}

float CrayfishDataSetUtils::fnotEqual(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (equals(val1, val2)) {
            return F_FALSE;
        } else {
            return F_TRUE;
        }
    }
}

float CrayfishDataSetUtils::fgreaterThan(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (val1 > val2) {
            return F_TRUE;
        } else {
            return F_FALSE;
        }
    }
}

float CrayfishDataSetUtils::flesserThan(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (val1 < val2) {
            return F_TRUE;
        } else {
            return F_FALSE;
        }
    }
}

float CrayfishDataSetUtils::flesserEqual(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (val1 <= val2) {
            return F_TRUE;
        } else {
            return F_FALSE;
        }
    }
}

float CrayfishDataSetUtils::fgreaterEqual(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        if (val1 >= val2) {
            return F_TRUE;
        } else {
            return F_FALSE;
        }
    }
}


float CrayfishDataSetUtils::flogicalAnd(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        bool bval1 = equals(val1, F_TRUE);
        bool bval2 = equals(val2, F_TRUE);
        if (bval1 && bval2)
            return F_TRUE;
        else
            return F_FALSE;
    }
}

float CrayfishDataSetUtils::flogicalOr(float val1, float val2) const {
    if (is_nodata(val1) || is_nodata(val2)) {
        return -9999.0f;
    } else {
        bool bval1 = equals(val1, F_TRUE);
        bool bval2 = equals(val2, F_TRUE);
        if (bval1 || bval2)
            return F_TRUE;
        else
            return F_FALSE;
    }
}

float CrayfishDataSetUtils::flogicalNot(float val1) const {
    if (is_nodata(val1)) {
        return -9999.0f;
    } else {
        bool bval1 = equals(val1, F_TRUE);
        if (bval1)
            return F_FALSE;
        else
            return F_TRUE;
    }
}

float CrayfishDataSetUtils::fchangeSign(float val1) const {
    if (is_nodata(val1))
        return -9999.0f;
    else
        return -val1;
}

float CrayfishDataSetUtils::fmin(float val1, float val2) const {
    if (is_nodata(val1)) {
        if (is_nodata(val2)) {
            return -9999.0f;
        } else {
            return val2;
        }
    } else {
        if (is_nodata(val2)) {
            return val1;
        } else {
            if (val1 > val2) {
                return val2;
            } else {
                return val1;
            }
        }
    }
}


float CrayfishDataSetUtils::fmax(float val1, float val2) const {
    if (is_nodata(val1)) {
        if (is_nodata(val2)) {
            return -9999.0f;
        } else {
            return val2;
        }
    } else {
        if (is_nodata(val2)) {
            return val1;
        } else {
            if (val1 < val2) {
                return val2;
            } else {
                return val1;
            }
        }
    }
}

float CrayfishDataSetUtils::fabs(float val1) const {
    if (is_nodata(val1))
        return -9999.0f;
    else
    {
        if (val1 > 0) {
            return val1;
        } else {
            return -val1;
        }
    }
}

float CrayfishDataSetUtils::fsum_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(-9999));
    Q_ASSERT(!vals.isEmpty());
    return std::accumulate(vals.begin(), vals.end(), 0.0);
}

float CrayfishDataSetUtils::fmin_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(-9999));
    Q_ASSERT(!vals.isEmpty());
    return *std::min_element(vals.begin(), vals.end());
}

float CrayfishDataSetUtils::fmax_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(-9999));
    Q_ASSERT(!vals.isEmpty());
    return *std::max_element(vals.begin(), vals.end());
}

float CrayfishDataSetUtils::favg_aggr(QVector<float>& vals) const {
    Q_ASSERT(!vals.contains(-9999));
    Q_ASSERT(!vals.isEmpty());
    return fsum_aggr(vals) / vals.size();
}

