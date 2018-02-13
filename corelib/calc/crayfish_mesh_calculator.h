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
#include "geos_c.h"

class CrayfishMeshCalculator
{
  public:

    //! Result of the calculation
    enum Result
    {
      Success = 0, //!< Calculation successful
      CreateOutputError = 1, //!< Error creating output data file
      InputLayerError = 2, //!< Error reading input layer
      ParserError = 3, //!< Error parsing formula
      InvalidDatasets = 4, //!< Datasets with different time outputs or not part of the mesh
      EvaluateError = 5, //!< Error during evaluation
      MemoryError = 6, //!< Error allocating memory for result
    };

    CrayfishMeshCalculator(const QString &formulaString, const QString &outputFile,
                            const BBox &outputExtent, float startTime, float endTime,
                            Mesh *mesh, bool addToMesh);

    CrayfishMeshCalculator(const QString &formulaString, const QString &outputFile,
                            const QString &maskWkt, float startTime, float endTime,
                            Mesh *mesh, bool addToMesh);

    /** Starts the calculation and writes new dataset to file, returns Result */
    Result processCalculation(const bool useMask = false);
    static Result expression_valid(const QString &formulaString, const Mesh *mesh);

  private:
    CrayfishMeshCalculator();

    QString mFormulaString; // expression
    QString mOutputFile;

    //! Spatial filter
    BBox mOutputExtent;
    //! Mask filter wkt
    QString mMaskWkt;

    //! Time filter
    float mStartTime;
    float mEndTime;

    //! Mesh
    Mesh* mMesh;

    //! Whether to add to the mesh
    bool mAddToMesh;
};

#endif // CRAYFISH_MESH_CALCULATOR_H
