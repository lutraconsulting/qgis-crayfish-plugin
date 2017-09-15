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

#include "calc/crayfish_mesh_calculator_node.h"
#include <cfloat>
#include "crayfish_output.h"

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode()
  : mType( tNoData )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mCondition( nullptr )
  , mNumber( 0 )
  , mOperator( opNONE )
{
}

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( double number )
  : mType( tNumber )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mCondition( nullptr )
  , mNumber( number )
  , mOperator( opNONE )
{
}


CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( Operator op, CrayfishMeshCalculatorNode *left, CrayfishMeshCalculatorNode *right )
  : mType( tOperator )
  , mLeft( left )
  , mRight( right )
  , mCondition( nullptr )
  , mNumber( 0 )
  , mOperator( op )
{
}

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode *condition /* bool condition */,
                                                        CrayfishMeshCalculatorNode *left /*if true */,
                                                        CrayfishMeshCalculatorNode *right /* if false */)
    : mType( tOperator )
    , mLeft( left )
    , mRight( right )
    , mCondition( condition )
    , mNumber( 0 )
    , mOperator( opIF )
{
}

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode(const QString &datasetName )
  : mType( tDatasetRef )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mCondition( nullptr )
  , mNumber( 0 )
  , mDatasetName( datasetName )
  , mOperator( opNONE )
{
  if ( mDatasetName.startsWith( '"' ) && mDatasetName.endsWith( '"' ) )
    mDatasetName = mDatasetName.mid( 1, mDatasetName.size() - 2 );
}

CrayfishMeshCalculatorNode::~CrayfishMeshCalculatorNode()
{
  if ( mLeft )
  {
    delete mLeft;
  }
  if ( mRight )
  {
    delete mRight;
  }
}

QStringList CrayfishMeshCalculatorNode::usedDatasetNames() const
{
    QStringList res;

    if (mType == tDatasetRef)
    {
        res.append(mDatasetName);
    }

    if ( mLeft )
    {
      res += mLeft->usedDatasetNames();
    }

    if ( mRight )
    {
      res += mRight->usedDatasetNames();
    }

    if (mCondition)
    {
      res += mCondition->usedDatasetNames();
    }

    return res;
}

bool CrayfishMeshCalculatorNode::calculate(const CrayfishDataSetUtils &dsu, DataSet& result, const DataSet& filter) const
{
  // note that filtering is done only when it affects the following operation.
  // final filtering of the result is done in the processCalculation()
  // to save some computation time

  if ( mType == tDatasetRef )
  {
      dsu.copy(result, mDatasetName);
      return true;
  }
  else if ( mType == tOperator )
  {
    DataSet leftDataset("left");
    DataSet rightDataset("right");


    if ( !mLeft || !mLeft->calculate( dsu, leftDataset, filter ) )
    {
        return false;
    }
    if ( mRight && !mRight->calculate( dsu, rightDataset, filter ) )
    {
        return false;
    }

    bool res;
    DataSet condition("condition");

    switch ( mOperator )
    {
        case opIF:
            // Evaluate boolean condition
            res = mCondition->calculate(dsu, condition, filter);
            if (!res) {
                // invalid boolean condition
                return false;
            }
            dsu.add_if(leftDataset, rightDataset, condition);
            break;

        case opPLUS:
            dsu.add(leftDataset, rightDataset);
            break;
        case opMINUS:
            dsu.subtract(leftDataset, rightDataset);
            break;
        case opMUL:
            dsu.multiply(leftDataset, rightDataset);
            break;
        case opDIV:
            dsu.divide(leftDataset, rightDataset);
            break;
        case opPOW:
            dsu.power(leftDataset, rightDataset);
            break;
        case opEQ:
            dsu.equal(leftDataset, rightDataset);
            break;
        case opNE:
            dsu.notEqual(leftDataset, rightDataset);
            break;
        case opGT:
            dsu.greaterThan(leftDataset, rightDataset);
            break;
        case opLT:
            dsu.lesserThan(leftDataset, rightDataset);
            break;
        case opGE:
            dsu.greaterEqual(leftDataset, rightDataset);
            break;
        case opLE:
            dsu.lesserEqual(leftDataset, rightDataset);
            break;
        case opAND:
            dsu.logicalAnd(leftDataset, rightDataset);
            break;
        case opOR:
            dsu.logicalOr(leftDataset, rightDataset);
            break;
        case opNOT:
            dsu.logicalNot(leftDataset);
            break;
        case opMIN:
            dsu.min(leftDataset, rightDataset);
            break;
        case opMAX:
            dsu.max(leftDataset, rightDataset);
            break;
        case opABS:
            dsu.abs(leftDataset);
            break;
        case opSUM_AGGR:
            // for aggr functions we need to filter before doing aggregation
            dsu.filter(leftDataset, filter);
            dsu.sum_aggr(leftDataset);
            break;
        case opMIN_AGGR:
            // for aggr functions we need to filter before doing aggregation
            dsu.filter(leftDataset, filter);
            dsu.min_aggr(leftDataset);
            break;
        case opMAX_AGGR:
            // for aggr functions we need to filter before doing aggregation
            dsu.filter(leftDataset, filter);
            dsu.max_aggr(leftDataset);
            break;
        case opAVG_AGGR:
            // for aggr functions we need to filter before doing aggregation
            dsu.filter(leftDataset, filter);
            dsu.avg_aggr(leftDataset);
            break;
        case opSIGN:
            dsu.changeSign(leftDataset);
            break;
        default:
            return false;
    }
    dsu.tranferOutputs(result, leftDataset);
    return true;
  }
  else if ( mType == tNumber )
  {
    dsu.number(result, mNumber);
    return true;
  }
  else if ( mType == tNoData )
  {
    dsu.nodata(result);
    return true;
  }

  // invalid type
  return false;
}

CrayfishMeshCalculatorNode *CrayfishMeshCalculatorNode::parseMeshCalcString( const QString &str, QString &parserErrorMsg )
{
  extern CrayfishMeshCalculatorNode *localParseMeshCalcString( const QString & str, QString & parserErrorMsg );
  return localParseMeshCalcString( str, parserErrorMsg );
}

