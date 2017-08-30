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

#include "calc/crayfish_mesh_calculator.h"
#include "calc/crayfish_mesh_calculator_node.h"


CrayfishMeshCalculator::CrayfishMeshCalculator( const QString &formulaString, const QString &outputFile,
    const BBox &outputExtent, float startTime, float endTime,
    const Mesh &mesh, bool addToMesh )
  : mFormulaString( formulaString )
  , mOutputFile( outputFile )
  , mOutputExtent( outputExtent )
  , mStartTime( startTime )
  , mEndTime( endTime )
  , mMesh( mesh )
  , mAddToMesh( addToMesh )
{
}

bool CrayfishMeshCalculator::expression_valid() {
    return true;
}

bool CrayfishMeshCalculator::processCalculation()
{
#if 0
  //prepare search string / tree
  QString errorString;
  CrayfishMeshCalculatorNode *calcNode = CrayfishMeshCalculatorNode::parseRasterCalcString( mFormulaString, errorString );
  if ( !calcNode )
  {
    //error
    return static_cast<int>( ParserError );
  }

  QMap< QString, QgsRasterBlock * > inputBlocks;
  QVector<CrayfishMeshCalculatorEntry>::const_iterator it = mRasterEntries.constBegin();
  for ( ; it != mRasterEntries.constEnd(); ++it )
  {
    if ( !it->raster ) // no raster layer in entry
    {
      delete calcNode;
      qDeleteAll( inputBlocks );
      return static_cast< int >( InputLayerError );
    }

    QgsRasterBlock *block = nullptr;
    // if crs transform needed
    if ( it->raster->crs() != mOutputCrs )
    {
      QgsRasterProjector proj;
      proj.setCrs( it->raster->crs(), mOutputCrs );
      proj.setInput( it->raster->dataProvider() );
      proj.setPrecision( QgsRasterProjector::Exact );

      block = proj.block( it->bandNumber, mOutputRectangle, mNumOutputColumns, mNumOutputRows );
    }
    else
    {
      block = it->raster->dataProvider()->block( it->bandNumber, mOutputRectangle, mNumOutputColumns, mNumOutputRows );
    }
    if ( block->isEmpty() )
    {
      delete block;
      delete calcNode;
      qDeleteAll( inputBlocks );
      return static_cast<int>( MemoryError );
    }
    inputBlocks.insert( it->ref, block );
  }

  //open output dataset for writing
  GDALDriverH outputDriver = openOutputDriver();
  if ( !outputDriver )
  {
    return static_cast< int >( CreateOutputError );
  }

  GDALDatasetH outputDataset = openOutputFile( outputDriver );
  GDALSetProjection( outputDataset, mOutputCrs.toWkt().toLocal8Bit().data() );
  GDALRasterBandH outputRasterBand = GDALGetRasterBand( outputDataset, 1 );

  float outputNodataValue = -FLT_MAX;
  GDALSetRasterNoDataValue( outputRasterBand, outputNodataValue );

  if ( p )
  {
    p->setMaximum( mNumOutputRows );
  }

  QgsRasterMatrix resultMatrix;
  resultMatrix.setNodataValue( outputNodataValue );

  //read / write line by line
  for ( int i = 0; i < mNumOutputRows; ++i )
  {
    if ( p )
    {
      p->setValue( i );
    }

    if ( p && p->wasCanceled() )
    {
      break;
    }

    if ( calcNode->calculate( inputBlocks, resultMatrix, i ) )
    {
      bool resultIsNumber = resultMatrix.isNumber();
      float *calcData = new float[mNumOutputColumns];

      for ( int j = 0; j < mNumOutputColumns; ++j )
      {
        calcData[j] = ( float )( resultIsNumber ? resultMatrix.number() : resultMatrix.data()[j] );
      }

      //write scanline to the dataset
      if ( GDALRasterIO( outputRasterBand, GF_Write, 0, i, mNumOutputColumns, 1, calcData, mNumOutputColumns, 1, GDT_Float32, 0, 0 ) != CE_None )
      {
        QgsDebugMsg( "RasterIO error!" );
      }

      delete[] calcData;
    }

  }

  if ( p )
  {
    p->setValue( mNumOutputRows );
  }

  //close datasets and release memory
  delete calcNode;
  qDeleteAll( inputBlocks );
  inputBlocks.clear();

  if ( p && p->wasCanceled() )
  {
    //delete the dataset without closing (because it is faster)
    GDALDeleteDataset( outputDriver, mOutputFile.toUtf8().constData() );
    return static_cast< int >( Canceled );
  }
  GDALClose( outputDataset );
#endif
  return static_cast< int >( Success );
}

CrayfishMeshCalculator::CrayfishMeshCalculator(){} /* forbidden */
