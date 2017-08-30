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

#ifndef CRAYFISH_MESH_CALCULATOR_NODE_H
#define CRAYFISH_MESH_CALCULATOR_NODE_H

#include <QMap>
#include <QString>

class CrayfishMeshCalculatorNode {
  public:
    //! defines possible types of node
    enum Type
    {
      tOperator = 1,
      tNumber,
      tRasterRef,
      tMatrix
    };

    //! possible operators
    enum Operator
    {
      opPLUS,
      opMINUS,
      opMUL,
      opDIV,
      opPOW,
      opSQRT,
      opSIN,
      opCOS,
      opTAN,
      opASIN,
      opACOS,
      opATAN,
      opEQ,         // =
      opNE,         //!=
      opGT,         // >
      opLT,         // <
      opGE,         // >=
      opLE,         // <=
      opAND,
      opOR,
      opSIGN,       // change sign
      opLOG,
      opLOG10,
      opNONE,
    };

    CrayfishMeshCalculatorNode();
    CrayfishMeshCalculatorNode( double number );
    CrayfishMeshCalculatorNode( QgsRasterMatrix *matrix );
    CrayfishMeshCalculatorNode( Operator op, CrayfishMeshCalculatorNode *left, CrayfishMeshCalculatorNode *right );
    CrayfishMeshCalculatorNode( const QString &rasterName );
    ~CrayfishMeshCalculatorNode();

    //! QgsRasterCalcNode cannot be copied
    CrayfishMeshCalculatorNode( const CrayfishMeshCalculatorNode &rh ) = delete;
    //! QgsRasterCalcNode cannot be copied
    CrayfishMeshCalculatorNode &operator=( const CrayfishMeshCalculatorNode &rh ) = delete;

    Type type() const { return mType; }

    //set left node
    void setLeft( CrayfishMeshCalculatorNode *left ) { delete mLeft; mLeft = left; }
    void setRight( CrayfishMeshCalculatorNode *right ) { delete mRight; mRight = right; }

    /** Calculates result of raster calculation (might be real matrix or single number).
     * \param rasterData input raster data references, map of raster name to raster data block
     * \param result destination raster matrix for calculation results
     * \param row optional row number to calculate for calculating result by rows, or -1 to
     * calculate entire result
     * \since QGIS 2.10
     * \note not available in Python bindings
     */
    bool calculate( QMap<QString, QgsRasterBlock * > &rasterData, QgsRasterMatrix &result, int row = -1 ) const;

    static CrayfishMeshCalculatorNode *parseMeshCalcString( const QString &str, QString &parserErrorMsg );

  private:
    Type mType;
    CrayfishMeshCalculatorNode *mLeft = nullptr;
    CrayfishMeshCalculatorNode *mRight = nullptr;
    double mNumber;
    QString mRasterName;
    QgsRasterMatrix *mMatrix = nullptr;
    Operator mOperator;
};


#endif // CRAYFISH_MESH_CALCULATOR_NODE_H
