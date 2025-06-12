#!/usr/bin/env python3
import os
import sys
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango
from netmon import InternetMonitor
from instance import SingleInstance




if __name__ == "__main__":
    # Manejar ejecución en Wayland
    if 'WAYLAND_DISPLAY' in os.environ:
        os.environ['XDG_SESSION_TYPE'] = 'x11'
    
    # Verificar instancia única antes de iniciar GTK
    lock = SingleInstance()
    if lock.already_running():
        print("Ya hay una instancia de la aplicación en ejecución.")
        # Mostrar notificación al usuario
        subprocess.run([
            'notify-send', 
            'Monitor de Internet',
            'Ya hay una instancia en ejecución'
        ])
        sys.exit(1)
    
    # Iniciar el bucle principal de GTK en el hilo principal
    Gtk.init()
    monitor = InternetMonitor()
    try:
        Gtk.main()
    finally:
        # Asegurarse de liberar el bloqueo al salir
        monitor.instance_lock.remove_lock()
