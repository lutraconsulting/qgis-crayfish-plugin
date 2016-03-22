#!/bin/bash
###########################################################################
#                                                                         #
#   This program is free software; you can redistribute it and/or modify  #
#   it under the terms of the GNU General Public License as published by  #
#   the Free Software Foundation; either version 2 of the License, or     #
#   (at your option) any later version.                                   #
#                                                                         #
###########################################################################

set -e

##### PYTHON

cd ../plugin
PYFILES=$(find . -type f -name "*.py" --max-depth=1)
for i in $PYFILES; do
    echo "$i"
    autopep8 --in-place --ignore=E261,E265,E402,E501 "$i"
done

##### C++
cd ../corelib
CFILES=$(find . -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" -or -name "*.c" \))

for i in ../**/*.cpp; do
    echo "$i"
    astyle --style=google --convert-tabs --indent=spaces=2 --preserve-date --suffix=none "$i"
done

cd ../scripts
