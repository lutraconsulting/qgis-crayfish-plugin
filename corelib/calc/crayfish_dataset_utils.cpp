#include "calc/crayfish_dataset_utils.h"


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

        if (ds->isTimeVarying()) {

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

        memset(output->getActive().data(), val == -9999, mMesh->elements().size()); // All cells active
        for (int i = 0; i < mMesh->nodes().size(); ++i) // Using for loop we are initializing
        {
            output->getValues()[i] = val;
        }
        dataset1.addOutput(output);
    } else {
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);
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


void CrayfishDataSetUtils::copy( DataSet& dataset1, const DataSet& dataset2 ) const {
    dataset1.deleteOutputs();

    for(int output_index=0; output_index < dataset2.outputCount(); ++output_index) {
        const Output* o0 = dataset2.constOutput(output_index);

        if (o0->type() == Output::TypeNode) {
            const NodeOutput* node_o0 = dataset2.constNodeOutput(output_index);

            NodeOutput* output = new NodeOutput();
            output->init(mMesh->nodes().size(),
                    mMesh->elements().size(),
                    DataSet::Scalar);

            for (int n=0; n<mMesh->nodes().size(); ++n)
            {
                output->getValues()[n] = node_o0->loadedValues()[n];
            }

            memset(output->getActive().data(), 1, mMesh->elements().size()); // All cells active
            dataset1.addOutput(output);

        } else {
            const ElementOutput* elem_o0 = dataset2.constElemOutput(output_index);

            ElementOutput* output = new ElementOutput();
            output->init(mMesh->elements().size(), false);
            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                output->getValues()[n] = elem_o0->loadedValues()[n];
            }

            dataset1.addOutput(output);
        }
    }
}


void CrayfishDataSetUtils::copy(DataSet& dataset1, const QString& datasetName) const {
    const DataSet* ds0 = dataset(datasetName);
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


Output* CrayfishDataSetUtils::canditateOutput(DataSet& dataset, int time_index) const {
    if (dataset.isTimeVarying()) {
        Q_ASSERT(dataset.outputCount() > time_index);

        return dataset.output(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.output(0);
    }
}

const Output* CrayfishDataSetUtils::constCanditateOutput(const DataSet& dataset, int time_index) const {
    if (dataset.isTimeVarying()) {
        Q_ASSERT(dataset.outputCount() > time_index);

        return dataset.constOutput(time_index);
    } else {
        Q_ASSERT(dataset.outputCount() == 1);
        return dataset.constOutput(0);
    }
}

int CrayfishDataSetUtils::outputTimesCount(const DataSet& dataset1, const DataSet& dataset2) const {
    if (dataset1.isTimeVarying() && dataset2.isTimeVarying()) {
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
                float res_val = -9999;
                if (val1 != -9999) {
                    res_val = func(val1);
                }
                nodeOutput->getValues()[n] = res_val;
            }

            // TODO activate
            memset(nodeOutput->getActive().data(), 1, mMesh->elements().size()); // All cells active

        } else {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(output);
            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, elemOutput);
                float res_val = -9999;
                if (val1 != -9999) {
                    res_val = func(val1);
                }
                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}


void CrayfishDataSetUtils::func2(DataSet& dataset1, const DataSet& dataset2, std::function<float(float,float)> func) const {
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
                float res_val = -9999;
                if ((val1 != -9999) && (val2 != -9999) ) {
                    res_val = func(val1, val2);
                }

                nodeOutput->getValues()[n] = res_val;
            }

            // TODO activate
            memset(nodeOutput->getActive().data(), 1, mMesh->elements().size()); // All cells active

        } else // o1->type() == Output::TypeElement
        {
            ElementOutput* elemOutput = static_cast<ElementOutput*>(o1);

            for (int n=0; n<mMesh->elements().size(); ++n)
            {
                float val1 = mMesh->valueAt(n, o1);
                float val2 = mMesh->valueAt(n, o2);
                float res_val = -9999;
                if ((val1 != -9999) && (val2 != -9999) ) {
                    res_val = func(val1, val2);
                }

                elemOutput->getValues()[n] = res_val;
            }
        }
    }
}

void CrayfishDataSetUtils::funcAggr(DataSet& dataset1, std::function<float(QVector<float>)> func) const {
    Output* o0 = canditateOutput(dataset1, 0);

    if (o0->type() == Output::TypeNode ) {
        QVector < float > vals;
        NodeOutput* output = new NodeOutput();
        output->init(mMesh->nodes().size(),
                mMesh->elements().size(),
                DataSet::Scalar);

        for (int n=0; n<mMesh->nodes().size(); ++n)
        {
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

        memset(output->getActive().data(), 1, mMesh->elements().size()); // All cells active
        dataset1.deleteOutputs();
        dataset1.addOutput(output);

    } else {
        QVector < float > vals;
        ElementOutput* output = new ElementOutput();
        output->init(mMesh->elements().size(), false);

        for (int n=0; n<mMesh->elements().size(); ++n)
        {
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
