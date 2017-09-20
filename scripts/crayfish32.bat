call c:\osgeo4w\osgeo4w.bat echo OSGEO4W
# call vs2010_64bit.bat
call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat"
path %path%;C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin

cd ..\corelib
nmake distclean
qmake -spec win32-msvc2012 "CONFIG+=release"
nmake

set /p CFVER=Crayfish package version:

python install.py -pkg=%CFVER%

pause
