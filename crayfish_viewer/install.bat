rem Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
rem Copyright (C) 2012 Peter Wells for Lutra Consulting

rem peter dot wells at lutraconsulting dot co dot uk
rem Lutra Consulting
rem 23 Chestnut Close
rem Burgess Hill
rem West Sussex
rem RH15 8HN

rem This program is free software; you can redistribute it and/or
rem modify it under the terms of the GNU General Public License
rem as published by the Free Software Foundation; either version 2
rem of the License, or (at your option) any later version.

rem This program is distributed in the hope that it will be useful,
rem but WITHOUT ANY WARRANTY; without even the implied warranty of
rem MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
rem GNU General Public License for more details.

rem You should have received a copy of the GNU General Public License
rem along with this program; if not, write to the Free Software
rem Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *

mkdir %HOMEPATH%\.qgis\python\plugins\crayfish
copy /y build\release\crayfishViewer.dll %HOMEPATH%\.qgis\python\plugins\crayfish
copy /y crayfishviewer.pyd %HOMEPATH%\.qgis\python\plugins\crayfish
PAUSE
