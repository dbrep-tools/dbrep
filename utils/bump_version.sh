#!/bin/bash

if [ -n "$1" ]; then
    sed -i 's/^__version__[[:space:]]*=[[:space:]]['\''"][0-9.]*['\''"]/__version__ = '\'$1\''/' ./dbrep/__init__.py
    poetry version $1
    echo "Versions set to $1"
    git commit -am "Updated version"
    git tag $1 
else
    echo "Must specify version in X.Y.Z format."
fi