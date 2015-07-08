@echo off
echo "Setting up 64-bit compilation environment with Visual C++ 2010 (Express) + Windows SDK 7.1"
set VC2010=c:\Program Files (x86)\Microsoft Visual Studio 10.0\VC
set SDK71=c:\Program Files\Microsoft SDKs\Windows\v7.1

set PATH="%VC2010%\bin\amd64";"%SDK71%\Bin\x64";%PATH%
set INCLUDE="%VC2010%\include";"%SDK71%\Include";%OSGEO4W_ROOT%\include
set LIB="%VC2010%\lib\amd64";"%SDK71%\Lib\x64"
