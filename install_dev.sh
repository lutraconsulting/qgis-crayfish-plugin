#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

case "$OSTYPE" in
    solaris*) ;;
    darwin*)  ln -s $DIR/crayfish ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/crayfish ;;
    linux*)   ln -s $DIR/crayfish ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/crayfish  ;;
    bsd*)     ;;
    msys*)    ;;
    *)        ;;
esac
