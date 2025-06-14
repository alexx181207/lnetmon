#!/bin/bash
set -e

# Crear entorno de construcción
APP="LNetMon"
VERSION="0.1.2"

#Crear directorio en el home del usuario si este no existe
[ ! -d "$HOME/LNetMon" ] && mkdir -p "$HOME/LNetMon"
DIR="$HOME/LNetMon/"
mkdir -p "$DIR/build"
APPDIR="$DIR/build/$APP.AppDir"
mkdir -p "$APPDIR/usr/bin/lnetmon"

#descomprimir depends y copiarlo al build
tar -xvf Depends.tar.xz -C $DIR
# Copiar archivos
cp -R $DIR/Depends/* "$APPDIR/"
cp -R src/* "$APPDIR/usr/bin/lnetmon"
#cp $HOME/appimagetool $DIR

# Crear AppRun
cat > "$APPDIR/AppRun" <<\EOF
#!/bin/bash

# Configurar rutas para librerías y GI
HERE="$(dirname "$(readlink -f "$0")")"

# Obtener información de la distribución

ID=$(grep '^ID=' /etc/os-release | awk -F= '{print $2}' | tr -d '"')
ID_LIKE=$(grep '^ID_LIKE=' /etc/os-release 2>/dev/null | awk -F= '{print $2}' | tr -d '"')

# Verificar si es derivada de Ubuntu
if [[ "$ID" == "ubuntu" ]];then
    export LD_LIBRARY_PATH="$HERE/usr/lib/ubuntu/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    export PYTHONPATH="$HERE/usr/lib/ubuntu/python3/dist-packages:$PYTHONPATH"
    export GI_TYPELIB_PATH="$HERE/usr/lib/ubuntu/x86_64-linux-gnu/girepository-1.0:${GI_TYPELIB_PATH}"
elif [[ "$ID_LIKE" =~ "ubuntu" ]];then
    export LD_LIBRARY_PATH="$HERE/usr/lib/ubuntu/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    export PYTHONPATH="$HERE/usr/lib/ubuntu/python3/dist-packages:$PYTHONPATH"
    export GI_TYPELIB_PATH="$HERE/usr/lib/ubuntu/x86_64-linux-gnu/girepository-1.0:${GI_TYPELIB_PATH}"
elif [[ "$ID_LIKE" =~ "debian" ]]; then
    export PYTHONPATH="$HERE/usr/lib/python3/dist-packages:$PYTHONPATH"
    export LD_LIBRARY_PATH="$HERE/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    export GI_TYPELIB_PATH="$HERE/lib/girepository-1.0:${GI_TYPELIB_PATH}"
else
    export LD_LIBRARY_PATH="$HERE/usr/lib:${LD_LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$HERE/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
    export GI_TYPELIB_PATH="$HERE/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"
    export PYTHONPATH="$HERE/usr/lib/python3.11/site-packages:$PYTHONPATH"
fi

exec "$HERE/usr/bin/lnetmon/main.py" "$@"

EOF
chmod +x "$APPDIR/AppRun"

# Crear .desktop"
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
wget -O $DIR/appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage

chmod +x $DIR/appimagetool

$DIR/appimagetool "$APPDIR" "$HOME/$APP-$VERSION.AppImage"

rm -rf $DIR/