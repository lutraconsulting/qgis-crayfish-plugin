#/bin/bash

set -u # Exit if we try to use an uninitialised variable
set -e # Return early if any command returns a non-0 exit status
PWD=`pwd`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CALC_DIR="$DIR/../corelib/calc"

command -v flex >/dev/null 2>&1 || { echo "I require flex but it's not installed. Aborting." >&2; exit 1; }
command -v bison >/dev/null 2>&1 || { echo "I require bison but it's not installed. Aborting." >&2; exit 1; }

cd $CALC_DIR/

# -d option for flex means that it will produce output to stderr while analyzing
flex -Pmesh -oflex_crayfish_mesh_calculator_lexer.cpp crayfish_mesh_calculator_lexer.ll


# bison options:
# -t add debugging facilities
# -d produce additional header file (used in parser.l)
# -v produce additional *.output file with parser states
bison -p mesh -obison_crayfish_mesh_calculator_parser.cpp -d -v -t crayfish_mesh_calculator_parser.yy

cd $PWD