/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2014 Lutra Consulting

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


#include "crayfish_eNp.h"

#include "math.h"
#include <QPointF>

#include <QVector3D>
#include <QVector2D>
#include <QPolygonF>
#include <limits>

static double ENP_contangent(QPointF a, QPointF b, QPointF c) {
    //http://geometry.caltech.edu/pubs/MHBD02.pdf
    QVector3D ba (b-a);
    QVector3D bc (b-c);

    double dp = QVector3D::dotProduct(bc, ba);
    QVector3D cp = QVector3D::crossProduct(bc, ba);

    return dp/cp.length();
}

bool ENP_physicalToLogical(const QPolygonF& pX, QPointF pP, QVector<double>& lam)
{
    //http://geometry.caltech.edu/pubs/MHBD02.pdf
    if (pX.size() < 3 || pX.size() != lam.size())
        return false;

    if (!pX.containsPoint(pP, Qt::WindingFill)) {
        return false;
    }

    double weightSum = 0;
    int prev = pX.size() -1;
    int next = 1;
    for (int i=0; i<pX.size(); i++)
    {
        double cotPrev = ENP_contangent(pP, pX[i], pX[prev]);
        double cotNext = ENP_contangent(pP, pX[i], pX[next]);
        double len2 = QVector2D(pX[i] - pP).lengthSquared();
        lam[i] = (cotPrev + cotNext) / len2;
        weightSum += lam[i];

        ++prev;
        if (prev == pX.size()) prev = 0;
        ++next;
        if (next == pX.size()) next = 0;
    }

    for (QVector<double>::iterator lamit=lam.begin(); lamit!=lam.end(); ++lamit)
    {
        *lamit = (*lamit)/weightSum;
    }

    return true;
}

static void ENP_centroid_step(const QPolygonF& pX, double& cx, double& cy, double& signedArea, int i, int i1)
{
    double x0 = 0.0; // Current vertex X
    double y0 = 0.0; // Current vertex Y
    double x1 = 0.0; // Next vertex X
    double y1 = 0.0; // Next vertex Y
    double a = 0.0;  // Partial signed area

    x0 = pX[i].x();
    y0 = pX[i].y();
    x1 = pX[i1].x();
    y1 = pX[i1].y();
    a = x0*y1 - x1*y0;
    signedArea += a;
    cx += (x0 + x1)*a;
    cy += (y0 + y1)*a;
}

void ENP_centroid(const QPolygonF& pX, double& cx, double& cy)
{
    // http://stackoverflow.com/questions/2792443/finding-the-centroid-of-a-polygon/2792459#2792459
    cx = 0;
    cy = 0;

    if (pX.isEmpty())
        return;

    double signedArea = 0.0;

    // For all vertices except last
    int i=0;
    for (; i<pX.size()-1; ++i)
    {
        ENP_centroid_step(pX, cx, cy, signedArea, i, i+1);
    }
    // Do last vertex separately to avoid performing an expensive
    // modulus operation in each iteration.
    ENP_centroid_step(pX, cx, cy, signedArea, i, 0);

    signedArea *= 0.5;
    cx /= (6.0*signedArea);
    cy /= (6.0*signedArea);
}
