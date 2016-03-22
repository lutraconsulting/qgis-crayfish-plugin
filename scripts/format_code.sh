#!/bin/bash
###########################################################################
#                                                                         #
#   This program is free software; you can redistribute it and/or modify  #
#   it under the terms of the GNU General Public License as published by  #
#   the Free Software Foundation; either version 2 of the License, or     #
#   (at your option) any later version.                                   #
#                                                                         #
###########################################################################

ASTYLEOPTS="--preserve-date
--indent-preprocessor
--brackets=break
--convert-tabs
--indent=spaces=2
--indent-classes
--indent-labels
--indent-namespaces
--indent-switches
--one-line=keep-blocks
--max-instatement-indent=40
--min-conditional-indent=-1
--suffix=none
--pad=oper
--pad=paren-in
--unpad=paren"

set -e

##### PYTHON

PYFILES=find .. -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" -or -name "*.c" \)
for i in $PYFILES; do
    echo "$i"
    autopep8 --in-place --ignore=E261,E265,E402,E501 "$i"
done

##### C++
CFILES=find .. -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" -or -name "*.c" \)

for i in ../**/*.cpp; do
    echo "$i"
    astyle --style=google --convert-tabs --indent=spaces=2 --preserve-date --suffix=none "$i"
done
