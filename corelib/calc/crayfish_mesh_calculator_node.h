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
#include <QStringList>

#include "crayfish_dataset.h"
#include "crayfish_mesh.h"
#include "calc/crayfish_dataset_utils.h"

class CrayfishMeshCalculatorNode {
  public:
    //! defines possible types of node
    enum Type
    {
      tOperator = 1,
      tNumber,
      tNoData,
      tDatasetRef
    };

    //! possible operators
    enum Operator
    {
      opPLUS,
      opMINUS,
      opMUL,        // *
      opDIV,        // /
      opPOW,        // ^
      opEQ,         // =
      opNE,         // !=
      opGT,         // >
      opLT,         // <
      opGE,         // >=
      opLE,         // <=
      opAND,
      opOR,
      opNOT,
      opIF,
      opSIGN,       // change sign
      opMIN,
      opMAX,
      opABS,
      opSUM_AGGR,
      opMAX_AGGR,
      opMIN_AGGR,
      opAVG_AGGR,
      opNONE,
    };

    CrayfishMeshCalculatorNode(); //NoDATA
    CrayfishMeshCalculatorNode( double number );
    CrayfishMeshCalculatorNode( Operator op, CrayfishMeshCalculatorNode *left, CrayfishMeshCalculatorNode *right );
    CrayfishMeshCalculatorNode( CrayfishMeshCalculatorNode *condition /* bool condition */,
                                CrayfishMeshCalculatorNode *left /*if true */,
                                CrayfishMeshCalculatorNode *right /* if false */);
    CrayfishMeshCalculatorNode( const QString &datasetName );
    ~CrayfishMeshCalculatorNode();

    Type type() const { return mType; }

    //set left node
    void setLeft( CrayfishMeshCalculatorNode *left ) { delete mLeft; mLeft = left; }
    void setRight( CrayfishMeshCalculatorNode *right ) { delete mRight; mRight = right; }

    /** Calculates result of mesh calculation
     * \param datasetData input dataset references, map of raster name to raster data block
     * \param result destination dataset for calculation results
     */
    bool calculate(const CrayfishDataSetUtils &dsu, DataSet &result) const;

    // Get all dataset names used
    QStringList usedDatasetNames() const;

    static CrayfishMeshCalculatorNode *parseMeshCalcString( const QString &str, QString &parserErrorMsg );

  private:
    Q_DISABLE_COPY(CrayfishMeshCalculatorNode)

    Type mType;
    CrayfishMeshCalculatorNode *mLeft;
    CrayfishMeshCalculatorNode *mRight;
    CrayfishMeshCalculatorNode *mCondition;
    double mNumber;
    QString mDatasetName;
    Operator mOperator;
};


#endif // CRAYFISH_MESH_CALCULATOR_NODE_H
