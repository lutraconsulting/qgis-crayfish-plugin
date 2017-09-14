/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2017 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#include <QFileInfo>

#include "calc/crayfish_mesh_calculator.h"
#include "calc/crayfish_mesh_calculator_node.h"
#include "crayfish_dataset.h"
#include "calc/crayfish_dataset_utils.h"
#include "crayfish.h"

CrayfishMeshCalculator::CrayfishMeshCalculator(const QString &formulaString, const QString &outputFile,
    const BBox &outputExtent, float startTime, float endTime,
    Mesh *mesh, bool addToMesh )
  : mFormulaString( formulaString )
  , mOutputFile( outputFile )
  , mOutputExtent( outputExtent )
  , mStartTime( startTime )
  , mEndTime( endTime )
  , mMesh( mesh )
  , mAddToMesh( addToMesh )
{
}

CrayfishMeshCalculator::Result CrayfishMeshCalculator::expression_valid(const QString &formulaString, const Mesh *mesh) {
    QString errorString;
    CrayfishMeshCalculatorNode *calcNode = CrayfishMeshCalculatorNode::parseMeshCalcString( formulaString, errorString );
    if ( !calcNode )
    {
      return ParserError;
    }

    CrayfishDataSetUtils dsu(mesh, calcNode->usedDatasetNames());
    if (!dsu.isValid()) {
        return InvalidDatasets;
    }

    return Success;
}

CrayfishMeshCalculator::Result CrayfishMeshCalculator::processCalculation()
{
  // check input
  if (mOutputFile.isEmpty()) {
        return CreateOutputError;
  }

  //prepare search string / tree
  QString errorString;
  CrayfishMeshCalculatorNode *calcNode = CrayfishMeshCalculatorNode::parseMeshCalcString( mFormulaString, errorString );
  if ( !calcNode )
  {
    return ParserError;
  }

  CrayfishDataSetUtils dsu(mMesh, calcNode->usedDatasetNames());
  if (!dsu.isValid()) {
      return InvalidDatasets;
  }

  //open output dataset
  DataSet* outputDataset = new DataSet(mOutputFile);

  DataSet filter("filter");
  dsu.ones(filter); // TODO use spatial&time flter

  // calculate
  bool ok = calcNode->calculate(dsu, *outputDataset, filter);
  if (!ok) {
      delete outputDataset;
      outputDataset = 0;
      return EvaluateError;
  }

  // Finalize dataset
  outputDataset->setMesh(mMesh);
  outputDataset->setType(DataSet::Scalar);
  outputDataset->setName(QFileInfo(mOutputFile).baseName());
  outputDataset->updateZRange();

  // store to file
  bool success = Crayfish::saveDataSet(mOutputFile, outputDataset);
  if (!success) {
    delete outputDataset;
    outputDataset = 0;

    return CreateOutputError;
  }

  // optionally add to the mesh
  if (mAddToMesh) {
      mMesh->addDataSet(outputDataset);
  } else {
      delete outputDataset;
      outputDataset = 0;
  }

  return Success;
}
