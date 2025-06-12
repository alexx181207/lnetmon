#!/bin/bash
set -e

# Crear entorno de construcción
APP="LNetMon"
VERSION="0.1.1"

#Crear directorio en el home del usuario si este no existe
[ ! -d "$HOME/LNetMon" ] && mkdir -p "$HOME/LNetMon"
DIR="$HOME/LNetMon/"
mkdir -p "$DIR/build"
APPDIR="$DIR/build/$APP.AppDir"
mkdir -p "$APPDIR/usr/bin/lnetmon"
#mkdir -p "$APPDIR/lib"
#mkdir -p "$APPDIR/usr/lib"
#mkdir -p "$APPDIR/usr/lib/x86_64-linux-gnu"
#mkdir -p "$APPDIR/lib/x86_64-linux-gnu"

#descomprimir depends y copiarlo al build
tar -xvf Depends.tar.xz -C $DIR
# Copiar archivos
cp -R $DIR/Depends/* "$APPDIR/"
cp -R src/* "$APPDIR/usr/bin/lnetmon"
cp $HOME/appimagetool $DIR

# Crear AppRun
cat > "$APPDIR/AppRun" <<\EOF
#!/bin/sh

# Configurar rutas para librerías y GI
HERE="$(dirname "$(readlink -f "$0")")"


if command -v apt &>/dev/null; then
    export PYTHONPATH="$HERE/usr/lib/python3/dist-packages:$PYTHONPATH"
    #export PYTHONPATH="$HERE/usr/bin/lnetmon:$PYTHONPATH"
    #export PYTHONPATH="$HERE/usr/lib/python3.11/site-packages:$PYTHONPATH"
    #export LD_LIBRARY_PATH="$HERE/lib:${LD_LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$HERE/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    #export LD_LIBRARY_PATH="$HERE/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    #export LD_LIBRARY_PATH="$HERE/usr/lib/python3/dist-packages:${LD_LIBRARY_PATH}"
    export GI_TYPELIB_PATH="$HERE/lib/girepository-1.0:${GI_TYPELIB_PATH}"
else
   export LD_LIBRARY_PATH="$HERE/usr/lib:${LD_LIBRARY_PATH}"
   export LD_LIBRARY_PATH="$HERE/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
   #export LD_LIBRARY_PATH="$HERE/usr/lib/python3/dist-packages:${LD_LIBRARY_PATH}"
   #export LD_LIBRARY_PATH="$HERE/lib/python3/dist-packages:${LD_LIBRARY_PATH}"
   export GI_TYPELIB_PATH="$HERE/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"
   export PYTHONPATH="$HERE/usr/lib/python3.11/site-packages:$PYTHONPATH"
    
fi

exec "$HERE/usr/bin/lnetmon/main.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Crear .desktop"$DIR"
cat > "$APPDIR/$APP.desktop" <<EOF
[Desktop Entry]
Name=LNetMon
Exec=AppRun
Icon=net-icon
Type=Application
Categories=Utility;
EOF

# Instalar dependencias en el AppDir
python3 -m pip install --target="$APPDIR/usr/lib/python3.11/site-packages" requests pystray pillow speedtest-cli psutil pygobject

# Descargar appimagetool
#wget -O $DIR/appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
#chmod +x build/appimagetool

# Construir AppImage
$DIR/appimagetool "$APPDIR" "$DIR/$APP-$VERSION.AppImage"

rm -rf $DIR/Depends
rm -rf $DIR/build