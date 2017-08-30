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

#ifndef CRAYFISH_MESH_CALCULATOR_H
#define CRAYFISH_MESH_CALCULATOR_H

#include <QString>
#include <QVector>
#include "crayfish_mesh.h"

struct CrayfishMeshCalculatorEntry
{
  QString ref; //name
  // QgsRasterLayer *raster; //pointer to rasterlayer
  int bandNumber; //raster band number
};

class CrayfishMeshCalculator
{
  public:

    //! Result of the calculation
    enum Result
    {
      Success = 0, //!< Calculation successful
      CreateOutputError = 1, //!< Error creating output data file
      InputLayerError = 2, //!< Error reading input layer
      Canceled = 3, //!< User canceled calculation
      ParserError = 4, //!< Error parsing formula
      MemoryError = 5, //!< Error allocating memory for result
    };

    CrayfishMeshCalculator( const QString &formulaString, const QString &outputFile,
                            const BBox &outputExtent, float startTime, float endTime,
                            const Mesh &mesh, bool addToMesh);

    /** Starts the calculation and writes new dataset to file, returns Result */
    int processCalculation();
    bool expression_valid();

  private:
    //default constructor forbidden. We need formula, output file, output format and output raster resolution obligatory
    CrayfishMeshCalculator();

    QString mFormulaString;
    QString mOutputFile;

    //! Spatial filter
    BBox mOutputRectangle;

    //! Time filter
    float mStartTime;
    float mEndTime;

    //! Whether to add to the mesh
    bool mAddToMesh;

    //! Mesh
    Mesh& mesh;

    /***/
    QVector<QgsRasterCalculatorEntry> mRasterEntries;
};

#endif // CRAYFISH_MESH_CALCULATOR_H
