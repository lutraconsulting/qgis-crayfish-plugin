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

typedef QMap<float, QVector<double> > timestep_map; //TIME (sorted), nodeVal


static void read(QDataStream& in, char* ptr, int len) {
    if( in.readRawData( ptr, len) != len )
        throw LoadStatus::Err_UnknownFormat;
}

static void ignore(QDataStream& in, int len) {
    QVector<char> ptr(len);
    read(in, (char*) ptr.data(), len);
}

static void file_boundary(QDataStream& in) {ignore(in, 3);}
static void record_boundary(QDataStream& in) {ignore(in, 4);}

static QString read_string(QDataStream& in, int len) {
    QVector<char> ptr(len);
    read(in, (char*) ptr.data(), len);
    return QString::fromUtf8(&ptr[0], len-1).trimmed();
}

static double read_real(QDataStream& in, size_t precision) {
    if (precision == sizeof(float))
    {
        float val;
        read(in, (char*)&val, precision);
        return val;
    } else {
        double val;
        read(in, (char*)&val, precision);
        return val;
    }
}

static int read_int(QDataStream& in) {
    int val;
    read(in, (char*)&val, sizeof(int));
    return val;
}


Mesh* Crayfish::loadSerafin(const QString& fileName, LoadStatus* status)
{
    // http://www.opentelemac.org/downloads/Archive/v6p0/telemac2d_user_manual_v6p0.pdf
    // Appendix 3

    if (status) status->clear();
    Mesh* mesh = 0;

    try
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
        QString varType = read_string(in, 8);
        size_t precision;
        if (varType == "SERAFIN") {
            precision = sizeof(float);
        } else if (varType == "SERAFIND") {
            precision = sizeof(double);
        } else {
            throw LoadStatus::Err_UnknownFormat;
        }
        record_boundary(in);

        /* 1 record containing the two integers NBV(1) and NBV(2) (number of linear
           and quadratic variables, NBV(2) with the value of 0 for Telemac, as
           quadratic values are not saved so far)
        */
        record_boundary(in);
        int NBV1 = read_int(in);
        int NBV2 = read_int(in);
        record_boundary(in);

        /* NBV(1) records containing the names and units of each variab
           le (over 32 characters)
        */
        QStringList var_names;
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
            IPARAM[i] = read_int(in);
        }
        int nLayers = IPARAM[7];
        int xOrigin = IPARAM[3];
        int yOrigin = IPARAM[4];
        int epsg = IPARAM[9];

        record_boundary(in);

        /*
          if IPARAM (10) = 1: a record containing the computation starting date
        */
        record_boundary(in);
        if (IPARAM[10] == 1) {
            int year = read_int(in);
            int month = read_int(in);
            int hour = read_int(in);
            int minute = read_int(in);
            int second = read_int(in);
            int milisecond = read_int(in);
        }
        record_boundary(in);

        /* 1 record containing the integers NELEM,NPOIN,NDP,1 (number of
           elements, number of points, number of points per element and the value 1)
         */
        record_boundary(in);
        int nElem = read_int(in);
        int nPoint = read_int(in);
        int nPointsPerElem = read_int(in);
        read_int(in); // dummy value 1
        record_boundary(in);

        /* 1 record containing table IKLE (integer array
           of dimension (NDP,NELEM)
           which is the connectivity table.

           Attention: in TELEMAC-2D, the dimensions of this array are (NELEM,NDP))
        */

        record_boundary(in);
        QVector<int> ikle(nElem*nPointsPerElem);
        read(in, (char*)ikle.data(), nElem*nPointsPerElem*sizeof(int));
        record_boundary(in);

        /* 1 record containing table IPOBO (integer array of dimension NPOIN); the
           value of one element is 0 for an internal point, and
           gives the numbering of boundary points for the others
        */

        record_boundary(in);
        QVector<int> iPointBoundary(nPoint);
        read(in, (char*)iPointBoundary.data(), nPoint*sizeof(int));
        record_boundary(in);

        /* 1 record containing table X (real array of dimension NPOIN containing the
           abscissae of the points)
        */

        record_boundary(in);
        QVector<double> x(nPoint);
        for (int i=0; i<nPoint; ++i)
        {
            x[i] = read_real(in, precision);
        }
        record_boundary(in);

        /* 1 record containing table Y (real array of dimension NPOIN containing the
           abscissae of the points)
        */

        record_boundary(in);
        QVector<double> y(nPoint);
        for (int i=0; i<nPoint; ++i)
        {
            y[i] = read_real(in, precision);
        }
        record_boundary(in);

        /* Next, for each time step, the following are found:
           - 1 record containing time T (real),
           - NBV(1)+NBV(2) records containing the results tables for each variable at time
        */
        /*
        int nTimesteps = 0;
        try {
         while(true) {
            float time = read_real(in, precision);

            QVector<timestep_map >

            read(in, (char*)&time, sizeof(float));

            nTimesteps ++;

         }
        } catch (LoadStatus::Error error) {
            //nothing to do
        }
        */
    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
