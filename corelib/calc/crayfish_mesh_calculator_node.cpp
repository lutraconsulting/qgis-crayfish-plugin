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

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode()
  : mType( tNumber )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mNumber( 0 )
  /* , mMatrix( nullptr ) */
  , mOperator( opNONE )
{
}

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( double number )
  : mType( tNumber )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mNumber( number )
  /* , mMatrix( nullptr ) */
  , mOperator( opNONE )
{
}

/*
CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( QgsRasterMatrix *matrix )
  : mType( tMatrix )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mNumber( 0 )
  , mMatrix( matrix )
  , mOperator( opNONE )
{

}
*/

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( Operator op, CrayfishMeshCalculatorNode *left, CrayfishMeshCalculatorNode *right )
  : mType( tOperator )
  , mLeft( left )
  , mRight( right )
  , mNumber( 0 )
  /* , mMatrix( nullptr ) */
  , mOperator( op )
{
}

CrayfishMeshCalculatorNode::CrayfishMeshCalculatorNode( const QString &rasterName )
  : mType( tRasterRef )
  , mLeft( nullptr )
  , mRight( nullptr )
  , mNumber( 0 )
  , mRasterName( rasterName )
  /* , mMatrix( nullptr ) */
  , mOperator( opNONE )
{
  if ( mRasterName.startsWith( '"' ) && mRasterName.endsWith( '"' ) )
    mRasterName = mRasterName.mid( 1, mRasterName.size() - 2 );
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

bool CrayfishMeshCalculatorNode::calculate( QMap<QString, DataSet * > &datasets, DataSet &result ) const
{
#if 0
  //if type is raster ref: return a copy of the corresponding matrix

  //if type is operator, call the proper matrix operations
  if ( mType == tRasterRef )
  {
    QMap<QString, QgsRasterBlock *>::iterator it = rasterData.find( mRasterName );
    if ( it == rasterData.end() )
    {
      return false;
    }

    int nRows = ( row >= 0 ? 1 : ( *it )->height() );
    int startRow = ( row >= 0 ? row : 0 );
    int endRow = startRow + nRows;
    int nCols = ( *it )->width();
    int nEntries = nCols * nRows;
    double *data = new double[nEntries];

    //convert input raster values to double, also convert input no data to result no data

    int outRow = 0;
    for ( int dataRow = startRow; dataRow < endRow ; ++dataRow, ++outRow )
    {
      for ( int dataCol = 0; dataCol < nCols; ++dataCol )
      {
        data[ dataCol + nCols * outRow] = ( *it )->isNoData( dataRow, dataCol ) ? result.nodataValue() : ( *it )->value( dataRow, dataCol );
      }
    }
    result.setData( nCols, nRows, data, result.nodataValue() );
    return true;
  }
  else if ( mType == tOperator )
  {
    QgsRasterMatrix leftMatrix, rightMatrix;
    leftMatrix.setNodataValue( result.nodataValue() );
    rightMatrix.setNodataValue( result.nodataValue() );

    if ( !mLeft || !mLeft->calculate( rasterData, leftMatrix, row ) )
    {
      return false;
    }
    if ( mRight && !mRight->calculate( rasterData, rightMatrix, row ) )
    {
      return false;
    }

    switch ( mOperator )
    {
      case opPLUS:
        leftMatrix.add( rightMatrix );
        break;
      case opMINUS:
        leftMatrix.subtract( rightMatrix );
        break;
      case opMUL:
        leftMatrix.multiply( rightMatrix );
        break;
      case opDIV:
        leftMatrix.divide( rightMatrix );
        break;
      case opPOW:
        leftMatrix.power( rightMatrix );
        break;
      case opEQ:
        leftMatrix.equal( rightMatrix );
        break;
      case opNE:
        leftMatrix.notEqual( rightMatrix );
        break;
      case opGT:
        leftMatrix.greaterThan( rightMatrix );
        break;
      case opLT:
        leftMatrix.lesserThan( rightMatrix );
        break;
      case opGE:
        leftMatrix.greaterEqual( rightMatrix );
        break;
      case opLE:
        leftMatrix.lesserEqual( rightMatrix );
        break;
      case opAND:
        leftMatrix.logicalAnd( rightMatrix );
        break;
      case opOR:
        leftMatrix.logicalOr( rightMatrix );
        break;
      case opSQRT:
        leftMatrix.squareRoot();
        break;
      case opSIN:
        leftMatrix.sinus();
        break;
      case opCOS:
        leftMatrix.cosinus();
        break;
      case opTAN:
        leftMatrix.tangens();
        break;
      case opASIN:
        leftMatrix.asinus();
        break;
      case opACOS:
        leftMatrix.acosinus();
        break;
      case opATAN:
        leftMatrix.atangens();
        break;
      case opSIGN:
        leftMatrix.changeSign();
        break;
      case opLOG:
        leftMatrix.log();
        break;
      case opLOG10:
        leftMatrix.log10();
        break;
      default:
        return false;
    }
    int newNColumns = leftMatrix.nColumns();
    int newNRows = leftMatrix.nRows();
    result.setData( newNColumns, newNRows, leftMatrix.takeData(), leftMatrix.nodataValue() );
    return true;
  }
  else if ( mType == tNumber )
  {
    double *data = new double[1];
    data[0] = mNumber;
    result.setData( 1, 1, data, result.nodataValue() );
    return true;
  }
  else if ( mType == tMatrix )
  {
    int nEntries = mMatrix->nColumns() * mMatrix->nRows();
    double *data = new double[nEntries];
    for ( int i = 0; i < nEntries; ++i )
    {
      data[i] = mMatrix->data()[i] == mMatrix->nodataValue() ? result.nodataValue() : mMatrix->data()[i];
    }
    result.setData( mMatrix->nColumns(), mMatrix->nRows(), data, result.nodataValue() );
    return true;
  }
  return false;
#endif
  return true;
}

CrayfishMeshCalculatorNode *CrayfishMeshCalculatorNode::parseMeshCalcString( const QString &str, QString &parserErrorMsg )
{
  extern CrayfishMeshCalculatorNode *localParseMeshCalcString( const QString & str, QString & parserErrorMsg );
  return localParseMeshCalcString( str, parserErrorMsg );
}

