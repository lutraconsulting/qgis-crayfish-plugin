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

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode *left /*if true */,
                            CrayfishMeshCalculatorNode *right /* if false */,
                            CrayfishMeshCalculatorNode *condition /* bool condition */)
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

    return res;
}

bool CrayfishMeshCalculatorNode::calculate(const CrayfishDataSetUtils &dsu, DataSet& result, const DataSet& filter) const
{
  if ( mType == tDatasetRef )
  {
      result = dsu.copy(mDatasetName);
      return true;
  }
  else if ( mType == tOperator )
  {
    DataSet leftDataset = dsu.nodata();
    DataSet rightDataset = dsu.nodata();

    if (mOperator == opIF) {
        DataSet true_condition("true_condition");
        bool res = mCondition->calculate(dsu, true_condition, dsu.ones());
        if (!res) {
            // invalid boolean condition
            return false;
        }

        DataSet false_condition = dsu.logicalNot(true_condition);

        DataSet true_filter = dsu.logicalAnd(filter, true_condition);
        DataSet false_filter = dsu.logicalAnd(filter, false_condition);

        if ( !mLeft || !mLeft->calculate( dsu, leftDataset, true_filter ) )
        {
          return false;
        }
        if ( mRight && !mRight->calculate( dsu, rightDataset, false_filter ) )
        {
          return false;
        }

        result = dsu.add(leftDataset, rightDataset);
        return true;

    } else {
        if ( !mLeft || !mLeft->calculate( dsu, leftDataset, filter ) )
        {
          return false;
        }
        if ( mRight && !mRight->calculate( dsu, rightDataset, filter ) )
        {
          return false;
        }

        switch ( mOperator )
        {
          case opPLUS:
            result = dsu.add(leftDataset, rightDataset);
            break;
          case opMINUS:
            result = dsu.subtract(leftDataset, rightDataset);
            break;
          case opMUL:
            result = dsu.multiply(leftDataset, rightDataset);
            break;
          case opDIV:
            result = dsu.divide(leftDataset, rightDataset);
            break;
          case opPOW:
            result = dsu.power(leftDataset, rightDataset);
            break;
          case opEQ:
            result = dsu.equal(leftDataset, rightDataset);
            break;
          case opNE:
            result = dsu.notEqual(leftDataset, rightDataset);
            break;
          case opGT:
            result = dsu.greaterThan(leftDataset, rightDataset);
            break;
          case opLT:
            result = dsu.lesserThan(leftDataset, rightDataset);
            break;
          case opGE:
            result = dsu.subtract(leftDataset, rightDataset);
            break;
          case opLE:
            result = dsu.lesserEqual(leftDataset, rightDataset);
            break;
          case opAND:
            result = dsu.logicalAnd(leftDataset, rightDataset);
            break;
          case opOR:
            result = dsu.logicalOr(leftDataset, rightDataset);
            break;
          case opNOT:
            result = dsu.logicalNot(leftDataset);
            break;
          case opMIN:
            result = dsu.min(leftDataset, rightDataset);
            break;
          case opMAX:
            result = dsu.max(leftDataset, rightDataset);
            break;
          case opABS:
            result = dsu.abs(leftDataset);
            break;
          case opSUM_AGGR:
            result = dsu.sum_aggr(leftDataset);
            break;
          case opMIN_AGGR:
            result = dsu.min_aggr(leftDataset);
            break;
          case opMAX_AGGR:
            result = dsu.max_aggr(leftDataset);
            break;
          case opAVG_AGGR:
            result = dsu.avg_aggr(leftDataset);
            break;
          case opSIGN:
            result = dsu.changeSign(leftDataset);
            break;
          default:
            return false;
        }
        return true;
    }
  }
  else if ( mType == tNumber )
  {
    result = dsu.number(mNumber);
  }
  else if ( mType == tNoData )
  {
    result = dsu.nodata();
  }
  return false;
}

CrayfishMeshCalculatorNode *CrayfishMeshCalculatorNode::parseMeshCalcString( const QString &str, QString &parserErrorMsg )
{
  extern CrayfishMeshCalculatorNode *localParseMeshCalcString( const QString & str, QString & parserErrorMsg );
  return localParseMeshCalcString( str, parserErrorMsg );
}

