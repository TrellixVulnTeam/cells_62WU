#!/bin/sh

set -e

PACKAGES_PATH=dist/packages/macos

cp .venv/lib/python3.7/site-packages/shiboken2/libshiboken2.abi*.dylib \
   .venv/lib/python3.7/site-packages/PySide2/ 

pyinstaller packaging/Cells.spec -y

cp ./packaging/macos/cells.sh ./dist/Cells.app/Contents/MacOS/

defaults write $PWD/dist/Cells.app/Contents/Info.plist CFBundleExecutable -string cells.sh

chmod -R 755 ./dist/Cells.app

mkdir -p $PACKAGES_PATH

# package application
pkgbuild --identifier by.alestsurko.cells \
         --install-location /Applications \
         --component dist/Cells.app \
         $PACKAGES_PATH/_cells.pkg

# package templates
mkdir -p /tmp/track_templates
pkgbuild --identifier by.alestsurko.cells.ctt \
         --install-location /tmp/track_templates \
         --scripts packaging/macos/scripts/ \
         --root track_templates \
         $PACKAGES_PATH/_templates.pkg

# synthesize Distribution.xml
productbuild --synthesize \
             --package $PACKAGES_PATH/_cells.pkg \
             --package $PACKAGES_PATH/_templates.pkg \
             $PACKAGES_PATH/Distribution.xml

# generate package
productbuild --distribution $PACKAGES_PATH/Distribution.xml \
             --package-path $PACKAGES_PATH \
             $PACKAGES_PATH/Cells.pkg

# clean up
rm -f $PACKAGES_PATH/_cells.pkg
rm -f $PACKAGES_PATH/_templates.pkg
rm -rf dist/Cells
rm -rf dist/Cells.app
