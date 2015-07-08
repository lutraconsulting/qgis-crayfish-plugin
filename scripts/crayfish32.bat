
call c:\osgeo4w\osgeo4w.bat echo OSGEO4W
call "c:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\vcvars32.bat"

cd ..\corelib
nmake distclean
qmake -spec win32-msvc2008 "CONFIG+=release"
nmake

set /p CFVER=Crayfish package version:

python install.py -pkg=%CFVER%

pause
