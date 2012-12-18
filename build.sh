#!/bin/bash

## Remove previous builds.  Start with clean slate.
rm -rf build dist

## Force python into 32 bit mode.
export VERSIONER_PYTHON_PREFER_32_BIT=yes

## Force build with custom installed python
#/System/Library/Frameworks/Python.framework/Versions/2.7/bin/python setup.py py2app
/usr/local/bin/python setup.py py2app

cwd=`pwd`
cd dist/aliens.app/Contents/Frameworks/
cp libmikmod.3.dylib libmikmod.dylib
cp libmikmod.3.dylib ../Resources/libmikmod.dylib
cd $cwd 

hdiutil create -imagekey zlib-level=9 -srcfolder dist/aliens.app dist/aliens.dmg
