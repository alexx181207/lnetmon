#!/bin/bash
set -e

# Crear entorno de construcción
APP="LNetMon"
VERSION="0.1.1"
APPDIR="/home/alejandro/Softwares/Proyecto/LNetMon/$APP.AppDir"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/lib"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/lib/x86_64-linux-gnu"
mkdir -p "$APPDIR/lib/x86_64-linux-gnu"

# Copiar archivos
cp lnetmon.py "$APPDIR/usr/bin"
cp Dependencias/net-icon.png "$APPDIR/usr/bin"
cp Dependencias/net-icon.png "$APPDIR"
chmod +x "$APPDIR/usr/bin/lnetmon.py"
cp Dependencias/librerias_necesarias/* "$APPDIR/usr/lib"
cp Dependencias/librerias_necesarias/* "$APPDIR/usr/lib/x86_64-linux-gnu"
cp Dependencias/librerias_necesarias/* "$APPDIR/lib/x86_64-linux-gnu"
cp -R Dependencias/include "$APPDIR/usr/"
cp -R Dependencias/share "$APPDIR/usr/"
cp -R Dependencias/pkgconfig "$APPDIR/usr/lib"
cp -R Dependencias/girepository-1.0 "$APPDIR/usr/lib"
cp -R Dependencias/girepository-1.0 "$APPDIR/lib"
cp -R Dependencias/pkgconfig "$APPDIR/lib"



# Crear AppRun
cat > "$APPDIR/AppRun" <<EOF
#!/bin/sh

# Configurar rutas para librerías y GI
HERE="\$(dirname "\$(readlink -f "\$0")")"
export LD_LIBRARY_PATH="$HERE/usr/lib:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="$HERE/lib:${LD_LIBRARY_PATH}"
export GI_TYPELIB_PATH="$HERE/usr/lib/girepository-1.0"
export GI_TYPELIB_PATH="$HERE/lib/girepository-1.0"
export XDG_DATA_DIRS="$HERE/usr/share:${XDG_DATA_DIRS}"
export PYTHONPATH="\$HERE/usr/lib/python3.11/site-packages:\$PYTHONPATH"

# Ejecutar la aplicación Python
exec "\$HERE/usr/bin/lnetmon.py"
EOF
chmod +x "$APPDIR/AppRun"

# Crear .desktop
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
#wget -O build/appimagetool https://github.com/AppImage/AppImageKit/releases/download/#continuous/appimagetool-x86_64.AppImage
#chmod +x build/appimagetool

# Construir AppImage
  /home/alejandro/Softwares/Proyecto/LNetMon/appimagetool "$APPDIR" "$APP-$VERSION.AppImage"
