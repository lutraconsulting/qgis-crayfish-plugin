
call c:\osgeo4w64\osgeo4w.bat echo OSGEO4W64
call vs2010_64bit.bat

cd ..\corelib
nmake distclean
qmake -spec win32-msvc2010 "CONFIG+=release"
nmake

set /p CFVER=Crayfish package version:

python install.py -pkg=%CFVER%

pause
