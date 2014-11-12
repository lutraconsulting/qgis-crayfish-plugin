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

#ifndef CRAYFISHVIEWER_GLOBAL_H
#define CRAYFISHVIEWER_GLOBAL_H

#include <QtCore/qglobal.h>
#include <QString>
#include <vector>


#if defined(CRAYFISHVIEWER_LIBRARY)
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_EXPORT
#else
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_IMPORT
#endif

namespace ElementType{
    enum Enum{
        Undefined,
        E4Q,
        E3T
    };
}


namespace DataSetType{
    enum Enum{
        Bed,
        Scalar,
        Vector
    };
}


enum VectorLengthMethod{
    MinMax,  //!< minimal and maximal length
    Scaled,  //!< length is scaled proportionally to the magnitude
    Fixed    //!< length is fixed to a certain value
};


#endif // CRAYFISHVIEWER_GLOBAL_H
