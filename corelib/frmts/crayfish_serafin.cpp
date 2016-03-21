/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2015 Lutra Consulting

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

#include "crayfish.h"

#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_mesh.h"

#include <QFile>
#include <QFileInfo>
#include <QScopedPointer>
#include <QTextStream>
#include <QVector>
#include <QStringList>
#include <QChar>

#include <math.h>

static inline bool is_equal(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}
typedef QMap<float, QVector<float> > timestep_map; //TIME (sorted), nodeVal

static void record_boundary(QDataStream& in) {
    int bread = in.skipRawData(4);
    if (bread != 4) {
        throw LoadStatus::Err_InvalidData;
    }
}

static QString read_string(QDataStream& in, int len) {
    QVector<char> ptr(len);

    if( in.readRawData( (char*) ptr.data(), len) != len )
        throw LoadStatus::Err_UnknownFormat;

    return QString::fromUtf8(&ptr[0], len).trimmed();
}

void parseFile(const QString& fileName,
               QStringList& var_names,
               int* xOrigin,
               int* yOrigin,
               int* nElem,
               int* nPoint,
               int* nPointsPerElem,
               QVector<int>& ikle,
               QVector<float>& x,
               QVector<float>& y,
               QVector<timestep_map>& data)
{
    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly))
      throw LoadStatus::Err_FileNotFound;  // Couldn't open the file
    QDataStream in(&file);

    /* 1 record containing the title of the study (72 characters) and a 8 characters
       string indicating the type of format (SERAFIN or SERAFIND)
    */
    record_boundary(in);
    QString title = read_string(in, 72);
    Q_UNUSED(title);
    QString varType = read_string(in, 8);
    if (varType == "SERAFIN") {
        in.setFloatingPointPrecision(QDataStream::SinglePrecision);
    } else if (varType == "SERAFIND") {
        in.setFloatingPointPrecision(QDataStream::DoublePrecision);
    } else {
        throw LoadStatus::Err_UnknownFormat;
    }
    record_boundary(in);

    /* 1 record containing the two integers NBV(1) and NBV(2) (number of linear
       and quadratic variables, NBV(2) with the value of 0 for Telemac, as
       quadratic values are not saved so far)
    */
    record_boundary(in);
    int NBV1, NBV2;
    in >> NBV1;
    in >> NBV2;
    record_boundary(in);

    /* NBV(1) records containing the names and units of each variab
       le (over 32 characters)
    */
    for (int i=0; i<NBV1; ++i)
    {
        record_boundary(in);
        var_names.push_back(read_string(in, 32));
        record_boundary(in);
    }

    /* 1 record containing the integers table IPARAM (10 integers, of which only
        the 6 are currently being used),

        - if IPARAM (3) != 0: the value corresponds to the x-coordinate of the
        origin of the mesh,

        - if IPARAM (4) != 0: the value corresponds to the y-coordinate of the
        origin of the mesh,

        - if IPARAM (7) != 0: the value corresponds to the number of  planes
        on the vertical (3D computation),

        - if IPARAM (8) != 0: the value corresponds to the number of
        boundary points (in parallel),

        - if IPARAM (9) != 0: the value corresponds to the number of interface
        points (in parallel),

        - if IPARAM(8) or IPARAM(9) != 0: the array IPOBO below is replaced
        by the array KNOLG (total initial number of points). All the other
        numbers are local to the sub-domain, including IKLE
    */

    record_boundary(in);

    int IPARAM[11]; // keep the numbering from the document
    for (int i = 1; i<11; ++i)
    {
        in >> IPARAM[i];
    }
    *xOrigin = IPARAM[3];
    *yOrigin = IPARAM[4];

    if (IPARAM[7] != 0) {
        // would need additional parsing
        throw LoadStatus::Err_MissingDriver;
    }

    record_boundary(in);


    /*
      if IPARAM (10) = 1: a record containing the computation starting date
    */
    record_boundary(in);
    if (IPARAM[10] == 1) {
        int dummy_date_data;
        in >> dummy_date_data; //year
        in >> dummy_date_data; //month
        in >> dummy_date_data; //hour
        in >> dummy_date_data; //minute
        in >> dummy_date_data; //second
        in >> dummy_date_data; //milisecond
        Q_UNUSED(dummy_date_data)
    }
    record_boundary(in);

    /* 1 record containing the integers NELEM,NPOIN,NDP,1 (number of
       elements, number of points, number of points per element and the value 1)
     */
    record_boundary(in);
    int dummy1;
    in >> *nElem;
    in >> *nPoint;
    in >> *nPointsPerElem;
    in >> dummy1;
    record_boundary(in);

    /* 1 record containing table IKLE (integer array
       of dimension (NDP,NELEM)
       which is the connectivity table.

       Attention: in TELEMAC-2D, the dimensions of this array are (NELEM,NDP))
    */

    record_boundary(in);
    ikle.resize((*nElem)*(*nPointsPerElem));
    for (int i=0; i< ikle.size(); ++i)
    {
        in >> ikle[i];
        -- ikle[i];  //numbered from 1
    }
    record_boundary(in);

    /* 1 record containing table IPOBO (integer array of dimension NPOIN); the
       value of one element is 0 for an internal point, and
       gives the numbering of boundary points for the others
    */

    record_boundary(in);
    QVector<int> iPointBoundary(*nPoint);
    for (int i=0; i< iPointBoundary.size(); ++i)
    {
        in >> iPointBoundary[i];
    }
    record_boundary(in);

    /* 1 record containing table X (real array of dimension NPOIN containing the
       abscissae of the points)
    */

    record_boundary(in);
    x.resize(*nPoint);
    for (int i=0; i<x.size(); ++i)
    {
        in >> x[i];
    }
    record_boundary(in);

    /* 1 record containing table Y (real array of dimension NPOIN containing the
       abscissae of the points)
    */

    record_boundary(in);
    y.resize(*nPoint);
    for (int i=0; i<y.size(); ++i)
    {
        in >> y[i];
    }
    record_boundary(in);

    /* Next, for each time step, the following are found:
       - 1 record containing time T (real),
       - NBV(1)+NBV(2) records containing the results tables for each variable at time
    */
    data.resize(var_names.size());
    int nTimesteps = in.device()->bytesAvailable() / (12 + (4 + (*nPoint) * 4 + 4) * var_names.size());
    for (int nT=0; nT< nTimesteps; ++nT) {
        record_boundary(in);
        float time;
        in >> time;
        record_boundary(in);

        for (int i=0; i<var_names.size(); ++i)
        {
            record_boundary(in);

            timestep_map& datait = data[i];
            QVector<float> datavals(*nPoint);
            for (int e=0; e<datavals.size(); ++e)
            {
                in >> datavals[e];
            }
            datait.insert(time, datavals);

            record_boundary(in);
        }
    }
}

static Mesh* createMesh(int xOrigin,
                        int yOrigin,
                        int nElems,
                        int nPoints,
                        int nPointsPerElem,
                        QVector<int>& ikle,
                        QVector<float>& x,
                        QVector<float>& y)
{
    Mesh::Nodes nodes(nPoints);
    Node* nodesPtr = nodes.data();
    for (int n = 0; n < nPoints; ++n, ++nodesPtr)
    {
        nodesPtr->setId(n);
        nodesPtr->x = xOrigin + x[n];
        nodesPtr->y = yOrigin + y[n];
    }

    Mesh::Elements elements(nElems);
    Element* elemPtr = elements.data();
    for (int e = 0; e < nElems; ++e, ++elemPtr)
    {
        if (nPointsPerElem != 3) {
            throw LoadStatus::Err_IncompatibleMesh; //we can add it, but it is uncommon for this format
        }

        elemPtr->setId(e);
        elemPtr->setEType(Element::E3T);
        for (int p=0; p<3; p++)
        {
            int val = ikle[e*3+p];
            if (val > nPoints - 1) {
                elemPtr->setP(p, 0);
            } else
            {
                elemPtr->setP(p, val);
            }
        }
    }

    return new Mesh(nodes, elements);
}

static void addData(Mesh* mesh, const QString& fileName, const QStringList& var_names, const QVector<timestep_map>& data, int nPoints, int nElems)
{
    for (int nName = 0; nName < var_names.size(); ++nName) {
        QString var_name(var_names[nName]);
        var_name = var_name.trimmed().toLower();

        bool is_vector = false;
        bool is_x = true;

        if (var_name.contains("velocity u") || var_name.contains("along x")) {
            is_vector = true;
            var_name = var_name.replace("velocity u", "velocity").replace("along x", "");
        }
        else if (var_name.contains("velocity v") || var_name.contains("along y")) {
            is_vector = true;
            is_x =  false;
            var_name = var_name.replace("velocity v", "velocity").replace("along y", "");
        }

        DataSet* dsd = mesh->dataSet(var_name);
        if (!dsd)
        {
            DataSet* dsd = new DataSet(fileName);
            dsd->setName(var_names[nName]);
            dsd->setType(is_vector ? DataSet::Vector : DataSet::Scalar);
            dsd->setIsTimeVarying(data[nName].size() > 1);
        }

        int i = 0;
        for (timestep_map::const_iterator it=data[nName].constBegin(); it != data[nName].constEnd(); ++it, ++i)
        {

            NodeOutput* tos = dsd->nodeOutput(i);
            if (!tos) {
                tos = new NodeOutput;
                tos->init(nPoints, nElems, false);
                tos->time = it.key();
                dsd->addOutput(tos);
            }

            for (int nP=0; nP<nPoints; nP++)
            {
                float val = it.value().at(nP);
                if (is_equal(val, 0)) {
                    val = -9999;
                }
                if (is_vector) {
                    if (is_x) {
                        tos->valuesV[nP].x = val;
                    } else {
                        tos->valuesV[nP].y = val;
                    }
                } else {
                    tos->values[nP] = val;
                }
            }

            memset(tos->active.data(), 1, nElems); // All cells active
        }
        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }
}

Mesh* Crayfish::loadSerafin(const QString& fileName, LoadStatus* status)
{
    // http://www.opentelemac.org/downloads/Archive/v6p0/telemac2d_user_manual_v6p0.pdf
    // Appendix 3

    if (status) status->clear();
    Mesh* mesh = 0;

    try
    {
        QStringList var_names;
        int xOrigin;
        int yOrigin;
        int nElems;
        int nPoints;
        int nPointsPerElem;
        QVector<int> ikle;
        QVector<float> x;
        QVector<float> y;
        QVector<timestep_map> data;
        parseFile(fileName,
                  var_names,
                  &xOrigin,
                  &yOrigin,
                  &nElems,
                  &nPoints,
                  &nPointsPerElem,
                  ikle,
                  x,
                  y,
                  data);

        mesh = createMesh(xOrigin,
                          yOrigin,
                          nElems,
                          nPoints,
                          nPointsPerElem,
                          ikle,
                          x,
                          y);

        addData(mesh, fileName, var_names, data, nPoints, nElems);
    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
