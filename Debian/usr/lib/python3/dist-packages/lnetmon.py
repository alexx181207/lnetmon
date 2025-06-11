#!/usr/bin/env python3
import os
import time
import subprocess
import threading
import requests
from PIL import Image, ImageDraw, ImageFilter
import pystray
import sys
import speedtest
import psutil
import json
from datetime import datetime, timedelta
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango
import base64
import io
import tempfile
import multiprocessing
import fcntl
import random

# Constantes de estilo
PRIMARY_COLOR = "#1E88E5"
SECONDARY_COLOR = "#66BB6A"
WARNING_COLOR = "#EF5350"
BACKGROUND_COLOR = "#F5F5F5"
DARK_MODE_BACKGROUND = "#1E1E1E"
FONT_FAMILY = "Inter, Roboto, Sans-Serif"
# Constantes para indicador de consumo de datos
"""DATA_CONSUMPTION_INDICATOR = {
    'green': '🟢',
    'yellow': '🟡',
    'red': '🔴'
}"""

class ModernIconGenerator:
    @staticmethod
    def generate_icon(color):
        """Crear ícono moderno con efectos visuales"""
        image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Efecto de sombra
        shadow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((15, 15, 113, 113), fill=(0, 0, 0, 30))
        shadow = shadow.filter(ImageFilter.GaussianBlur(5))
        
        # Círculo principal con degradado
        gradient = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for i in range(30):
            alpha = int(255 * (1 - i/30))
            gradient_draw.ellipse(
                (10+i, 10+i, 118-i, 118-i),
                fill=(*tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)), alpha)
            )
        
        # Círculo interior
        dc.ellipse((20, 20, 108, 108), 
                  fill=(*tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)), 255))
        
        # Efecto de brillo
        dc.ellipse((40, 40, 88, 88), fill=(255, 255, 255, 60))
        
        # Combinar sombras y gradientes
        result = Image.alpha_composite(shadow, gradient)
        result = Image.alpha_composite(result, image)
        return result.resize((64, 64), Image.LANCZOS)

def create_icon_file():
    """Crear archivo de ícono si no existe con estilo moderno"""
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "net_icon.png")
    if not os.path.exists(icon_path):
        try:
            ModernIconGenerator.generate_icon(PRIMARY_COLOR).save(icon_path)
            print(f"Ícono moderno creado en: {icon_path}")
        except Exception as e:
            print(f"No se pudo crear el ícono: {e}")
            

def generate_rounded_rectangle(draw, xy, radius, fill):
    """Dibuja un rectángulo con esquinas redondeadas"""
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)  # Centro horizontal
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)  # Centro vertical
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)  # Esquina superior izquierda
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)  # Esquina superior derecha
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)  # Esquina inferior izquierda
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)  # Esquina inferior derecha

def generate_bar_chart_icon(size=64, color="#1E88E5"):
    """Genera un ícono de gráfico de barras con esquinas redondeadas"""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    bar_width = size // 8
    spacing = size // 12
    max_height = int(size * 0.8)
    corner_radius = 2

    bars = [0.3, 0.7, 0.5, 0.9, 0.6]  # Alturas simuladas

    for i, height_ratio in enumerate(bars):
        x0 = spacing + i * (bar_width + spacing)
        x1 = x0 + bar_width
        y0 = size - (height_ratio * max_height)
        y1 = size

        generate_rounded_rectangle(draw, (x0, y0, x1, y1), corner_radius, fill=color)

    return image

"""def generate_bar_chart_icon(size=64, color="#1E88E5"):
    
    #Genera un ícono de gráfico de barras para estadísticas mensuales
    
    # Crear imagen RGBA transparente
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bar_width = size // 8
    spacing = size // 12
    max_height = int(size * 0.8)
    
    # Datos simulados de barras
    bars = [0.3, 0.7, 0.5, 0.9, 0.6]

    for i, height_ratio in enumerate(bars):
        x0 = spacing + i * (bar_width + spacing)
        x1 = x0 + bar_width
        y0 = size - (height_ratio * max_height)
        y1 = size

        draw.rectangle(
            [(x0, y0), (x1, y1)],
            fill=color,
            radius=2
        )

    return img"""

def get_bar_chart_icon_pixbuf(size=64, color="#1E88E5"):
    """
    Devuelve un Gtk Pixbuf del icono de gráfico de barras
    """
    image = generate_bar_chart_icon(size, color)
    
    # Convertir a Pixbuf
    data = image.tobytes()
    w, h = image.size
    data = GLib.Bytes.new(data)
    pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
        data,
        GdkPixbuf.Colorspace.RGB,
        True,  # has_alpha
        8,     # bits_per_sample
        w, h, w * 4
    )
    return pixbuf.scale_simple(32, 32, GdkPixbuf.InterpType.BILINEAR)
"""
def generate_info_icon(size=64, color="#1E88E5"):
    #Genera un ícono de información (i dentro de círculo)
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Círculo exterior
    draw.ellipse((0, 0, size, size), fill=color)

    # Círculo interior blanco para la "i"
    inner_size = size // 2
    inner_radius = inner_size // 2
    x = (size - inner_size) // 2
    y = (size - inner_size) // 2
    draw.ellipse((x, y, x + inner_size, y + inner_size), fill="white")

    # Línea vertical de la "i"
    line_width = max(2, size // 16)
    line_x = size // 2
    line_y_start = y + inner_size + 4
    line_y_end = size - 8
    draw.line([(line_x, line_y_start), (line_x, line_y_end)], fill="white", width=line_width)

    return image

def get_info_icon_pixbuf(size=64, color="#1E88E5"):
    Devuelve un Gtk Pixbuf del ícono de información
    image = generate_info_icon(size, color)
    
    # Convertir a Pixbuf
    data = image.tobytes()
    w, h = image.size
    data = GLib.Bytes.new(data)
    pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
        data,
        GdkPixbuf.Colorspace.RGB,
        True,  # has_alpha
        8,     # bits_per_sample
        w, h, w * 4
    )
    return pixbuf.scale_simple(32, 32, GdkPixbuf.InterpType.BILINEAR)"""

class SingleInstance:
    def __init__(self, lockfile=None):
        self.lockfile = lockfile or os.path.join(tempfile.gettempdir(), "internet-monitor.lock")
        self.fd = None

    def already_running(self):
        if os.path.exists(self.lockfile):
            try:
                with open(self.lockfile, 'r') as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    return True
            except:
                pass
        try:
            os.unlink(self.lockfile)
        except:
            pass
        return False

    def create_lock(self):
        try:
            self.fd = open(self.lockfile, 'w')
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, BlockingIOError):
                return False
            return True
        except Exception as e:
            print(f"Error creando bloqueo: {e}")
            return False

    def remove_lock(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except:
                pass
        try:
            os.unlink(self.lockfile)
        except:
            pass

class ModernStyleProvider:
    @staticmethod
    def get_css():
        return """
        window.background {
            background-color: @bg_color;
        }
        button {
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        button:hover {
            background-color: shade(@primary_color, 1.1);
        }
        .card {
            background-color: alpha(@bg_color, 0.95);
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 8px;
        }
        .status-label {
            font-size: 18px;
            font-weight: 600;
        }
        .value-label {
            font-size: 24px;
            font-weight: 700;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: @primary_color;
            margin-bottom: 8px;
        }
        .history-row {
            padding: 10px;
            border-bottom: 1px solid alpha(#aaa, 0.1);
        }
        .history-row:last-child {
            border-bottom: none;
        }
        switch {
            min-height: 24px;
            min-width: 48px;
        }
        .dark-mode {
            background-color: @dark_bg;
        }
        .dark-mode .card {
            background-color: shade(@dark_bg, 1.05);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .header-bar {
            min-height: 28px;
            padding: 0px;
            font-size: 12px;
        }
        .header-bar button {
            min-width: 28px;
            min-height: 28px;
            padding: 0px;
        }
        .window-frame {
            border-width: 0px;
        }
        .dialog-action-area button {
            min-width: 80px;
            min-height: 30px;
            font-size: 12px;
            padding: 2px 8px;
        }
        """

    @staticmethod
    def apply_styles(dark_mode=False):
        
        css_provider = Gtk.CssProvider()
        #css_provider.load_from_data(css.encode())
        #Gtk.StyleContext.add_provider_for_screen(
        #    Gdk.Screen.get_default(),
         #   css_provider,
         #   Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        #)
        # Crear CSS dinámico reemplazando variables manualmente
        css = ModernStyleProvider.get_css()
        css = css.replace("@bg_color", BACKGROUND_COLOR if not dark_mode else DARK_MODE_BACKGROUND)
        css = css.replace("@dark_bg", DARK_MODE_BACKGROUND)
        css = css.replace("@primary_color", PRIMARY_COLOR)

        try:
            css_provider.load_from_data(css.encode())
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Error al aplicar estilos: {e}")

class InternetMonitor:
    CONFIG_FILE = os.path.expanduser("~/.config/internet-monitor/config.json")
    DATA_CONSUMPTION_INDICATOR = {
        'green': '🟢',
        'yellow': '🟡',
        'red': '🔴'
    }

    def __init__(self):
        self.instance_lock = SingleInstance()
        if self.instance_lock.already_running():
            print("Ya hay una instancia de la aplicación en ejecución. Saliendo.")
            sys.exit(1)
            
        if not self.instance_lock.create_lock():
            print("No se pudo crear el bloqueo. Saliendo.")
            sys.exit(1)

        self.config = self.load_config()
        self.dark_mode = self.config.get('dark_mode', False)
        ModernStyleProvider.apply_styles(self.dark_mode)
        
        # Variables de estado
        self.connected = None
        self.vpn_active = False
        self.icon = None
        self.running = True
        self.blink_state = False
        self.blink_active = False
        self.last_speed_test = None
        self.speed_results = None
        self.start_time = datetime.now()
        self.connection_history = []
        self.gui_window = None
        self.gui_update_id = None
        self.last_vpn_check = datetime.min
        self.speed_test_in_progress = False
        self.speed_test_queue = multiprocessing.Queue()
        self.speed_test_process = None
        
        # Cargar historial de consumo
        self.data_history = self.load_data_history()
        
        # Asegurar que app_stats exista
        if "app_stats" not in self.data_history:
            self.data_history["app_stats"] = {}
        
        # Estadísticas de consumo de datos
        self.total_downloaded = 0
        self.total_uploaded = 0
        self.data_threshold = self.config.get('data_threshold', 1024)
        self.threshold_exceeded = False
        self.last_data_reset = datetime.now()
        
        # Crear imágenes para el ícono
        self.connected_image = ModernIconGenerator.generate_icon("#43A047")
        self.disconnected_image = ModernIconGenerator.generate_icon("#E53935")
        self.blink_off_image = ModernIconGenerator.generate_icon("#000000")
        self.vpn_image = ModernIconGenerator.generate_icon("#1E88E5")
        
        self.window_icon = self.create_window_icon()
        
        # Iniciar hilos
        self.monitor_thread = threading.Thread(target=self.monitor_connection)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.blink_thread = threading.Thread(target=self.blink_icon)
        self.blink_thread.daemon = True
        self.blink_thread.start()
        
        self.speed_thread = threading.Thread(target=self.periodic_speed_test)
        self.speed_thread.daemon = True
        self.speed_thread.start()
        
        self.resource_thread = threading.Thread(target=self.monitor_resources)
        self.resource_thread.daemon = True
        self.resource_thread.start()
        
        self.result_check_thread = threading.Thread(target=self.check_speed_test_results)
        self.result_check_thread.daemon = True
        self.result_check_thread.start()
        
        self.data_check_thread = threading.Thread(target=self.periodic_data_check)
        self.data_check_thread.daemon = True
        self.data_check_thread.start()
        
        self.app_data_thread = threading.Thread(target=self.monitor_app_data)
        self.app_data_thread.daemon = True
        self.app_data_thread.start()
        
        self.data_usage_menu_item = pystray.MenuItem('', lambda: None)  # Referencia al ítem de consumo de datos
        
    
        # Inicializar contadores desde historial
        current_month = datetime.now().strftime("%Y-%m")
        if self.data_history["current_month"] == current_month:
            self.total_downloaded = float(self.data_history["total_downloaded"])
            self.total_uploaded = float(self.data_history["total_uploaded"])
        else:
            self.reset_data_counters(reset_all=False)  # Solo reiniciar mes actual
        
        # Iniciar ícono del sistema
        self.start_system_tray()

    def create_window_icon(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "net_icon.png")
            
            # Cargar y escalar con alta calidad
            if os.path.exists(icon_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 32, 32)
                return pixbuf
            return Gtk.IconTheme.get_default().load_icon("network-wireless", 32, 0)
        except Exception as e:
            print(f"Error cargando ícono: {e}")
            return None
    
    def load_config(self):
        default_config = {
            'check_interval': 5,
            'blink_interval': 0.5,
            'speed_test_interval': 5000,
            'low_speed_threshold': 2,
            'auto_restart_threshold': 3,
            'vpn_check': True,
            'notifications': True,
            'show_gui_on_start': False,
            'vpn_check_interval': 10,
            'data_threshold': 1024,
            'daily_reset': True,
            'auto_disconnect': False,
            'dark_mode': False,
            'theme_color': PRIMARY_COLOR
        }
        
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE) as f:
                    loaded_config = json.load(f)
                    if 'data_threshold' in loaded_config and loaded_config['data_threshold'] < 100:
                        loaded_config['data_threshold'] *= 1024
                    return {**default_config, **loaded_config}
        except:
            pass
        return default_config

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    def check_internet(self):
        test_urls = [
            'https://www.cloudflare.com', 
            'https://www.google.com', 
            'https://www.apple.com' 
        ]
        
        for url in test_urls:
            try:
                requests.head(url, timeout=2)
                return True
            except (requests.ConnectionError, requests.Timeout):
                continue
        return False

    def check_vpn(self):
        if (datetime.now() - self.last_vpn_check).total_seconds() < self.config['vpn_check_interval']:
            return self.vpn_active
            
        self.last_vpn_check = datetime.now()
        new_status = False
        
        try:
            interfaces = psutil.net_if_stats()
            for interface in interfaces:
                if "tun" in interface or "vpn" in interface.lower():
                    new_status = True
                    break
            
            if not new_status:
                for route in psutil.net_if_addrs().items():
                    for addr in route[1]:
                        if addr.family == 2 and ("tun" in route[0] or "vpn" in route[0].lower()):
                            new_status = True
                            break
            
            if not new_status:
                for proc in psutil.process_iter(['name']):
                    name = proc.info['name'].lower()
                    if "openvpn" in name or "wireguard" in name or "vpn" in name:
                        new_status = True
                        break
            
            if not new_status:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.raddr and conn.raddr.port in [1194, 51820]:
                        new_status = True
                        break
            
            if new_status != self.vpn_active:
                self.vpn_active = new_status
                if self.gui_window:
                    GLib.idle_add(self.update_gui)
        except Exception as e:
            print(f"Error verificando VPN: {e}")
        
        return self.vpn_active

    def send_notification(self, title, message):
        if not self.config['notifications']:
            return
            
        try:
            subprocess.run([
                'notify-send', 
                '-i', 'network-wireless',
                title,
                message
            ], check=True)
        except:
            pass

    def run_speed_test_process(self, queue):
        try:
            st = speedtest.Speedtest()
            st.config['download_timeout'] = 15
            st.config['upload_timeout'] = 10
            st.get_best_server()
            download_speed = st.download() / 1_000_000
            upload_speed = st.upload() / 1_000_000
            ping = st.results.ping
            
            queue.put({
                'download': download_speed,
                'upload': upload_speed,
                'ping': ping,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error en test de velocidad: {e}")
            queue.put(None)

    def run_speed_test_now(self, icon=None, item=None):
        if self.speed_test_in_progress:
            return
            
        self.speed_test_in_progress = True
        
        if self.gui_window:
            GLib.idle_add(self.show_speed_test_progress)
        
        self.speed_test_process = multiprocessing.Process(
            target=self.run_speed_test_process,
            args=(self.speed_test_queue,)
        )
        self.speed_test_process.start()

    def check_speed_test_results(self):
        while self.running:
            if self.speed_test_process and not self.speed_test_queue.empty():
                result = self.speed_test_queue.get()
                if result:
                    self.speed_results = result
                    self.last_speed_test = datetime.now()
                    
                    if self.speed_results['download'] < self.config['low_speed_threshold']:
                        self.send_notification(
                            "Velocidad de Internet Baja",
                            f"Descarga: {self.speed_results['download']:.2f} Mbps (Umbral: {self.config['low_speed_threshold']} Mbps)"
                        )
                
                if self.gui_window:
                    GLib.idle_add(self.update_gui)
                
                self.speed_test_process = None
                self.speed_test_in_progress = False
            time.sleep(1)

    def show_speed_test_progress(self):
        if not self.gui_window:
            return
            
        self.download_label.set_text("Realizando test...")
        self.upload_label.set_text("Por favor espera")
        self.ping_label.set_text("")
        self.last_test_label.set_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.test_button.set_sensitive(False)

    def periodic_speed_test(self):
        while self.running:
            if self.connected and not self.speed_test_in_progress:
                time.sleep(5)
                queue = multiprocessing.Queue()
                process = multiprocessing.Process(
                    target=self.run_speed_test_process,
                    args=(queue,)
                )
                process.start()
                
                process.join(timeout=60)
                if queue.empty():
                    print("Test periódico de velocidad falló o excedió el tiempo")
                else:
                    result = queue.get()
                    if result:
                        self.speed_results = result
                        self.last_speed_test = datetime.now()
                        
                        if self.speed_results['download'] < self.config['low_speed_threshold']:
                            self.send_notification(
                                "Velocidad de Internet Baja",
                                f"Descarga: {self.speed_results['download']:.2f} Mbps (Umbral: {self.config['low_speed_threshold']} Mbps)"
                            )
                        
                        if self.gui_window:
                            GLib.idle_add(self.update_gui)
            time.sleep(self.config['speed_test_interval'])

    def monitor_resources(self):
        prev_stats = psutil.net_io_counters()
        prev_time = time.time()
        MAX_INTERVAL = 60  # Segundos máximos entre mediciones
        OVERHEAD_FACTOR = 1.05  # Ajuste por overhead de red

        
        while self.running:
            time.sleep(5)
            current_stats = psutil.net_io_counters()
            current_time = time.time()
            elapsed = current_time - prev_time
            current_usage = self.get_app_data_usage()
            
            for app, data in current_usage.items():
                if app not in self.data_history["app_stats"]:
                    self.data_history["app_stats"][app] = {"download": 0, "upload": 0, "total": 0}
            
                # Redondear antes de acumular
                self.data_history["app_stats"][app]["download"] = round(
                    self.data_history["app_stats"][app]["download"] + data["download"], 2
                )
                self.data_history["app_stats"][app]["upload"] = round(
                    self.data_history["app_stats"][app]["upload"] + data["upload"], 2
                )
                self.data_history["app_stats"][app]["total"] = round(
                    self.data_history["app_stats"][app]["download"] + self.data_history["app_stats"][app]["upload"], 2
                )
            
            # Manejar intervalos largos (suspensión)
            if elapsed > MAX_INTERVAL:
                elapsed = MAX_INTERVAL
        
            # Función segura para reset de contadores
            def safe_delta(new, old):
                return (new - old) if new >= old else new
            
            download_speed = (current_stats.bytes_recv - prev_stats.bytes_recv) / elapsed / 1024
            upload_speed = (current_stats.bytes_sent - prev_stats.bytes_sent) / elapsed / 1024
            
            # Calcular datos con overhead
            dl_bytes = safe_delta(current_stats.bytes_recv, prev_stats.bytes_recv) * OVERHEAD_FACTOR
            ul_bytes = safe_delta(current_stats.bytes_sent, prev_stats.bytes_sent) * OVERHEAD_FACTOR
        
            downloaded_mb = dl_bytes / (1024 * 1024)
            uploaded_mb = ul_bytes / (1024 * 1024)
            
            self.total_downloaded += downloaded_mb
            self.total_uploaded += uploaded_mb
            self.data_history["total_downloaded"] = float(self.total_downloaded)
            self.data_history["total_uploaded"] = float(self.total_uploaded)
            
            total_data = self.total_downloaded + self.total_uploaded
            
            if (total_data >= self.data_threshold and not self.threshold_exceeded and 
                self.config['notifications']):
                self.threshold_exceeded = True
                self.send_notification(
                    "¡Umbral de Datos Excedido!",
                    f"Has consumido {total_data:.2f} MB de datos (Umbral: {self.data_threshold} MB)\n"
                    f"Descarga: {self.total_downloaded:.2f} MB | Subida: {self.total_uploaded:.2f} MB"
                )
                
                if self.config['auto_disconnect']:
                    self.disconnect_network()
            
            if self.config['daily_reset'] and datetime.now().date() > self.last_data_reset.date():
                self.reset_data_counters()
            
            if self.gui_window:
                GLib.idle_add(self.update_network_usage, download_speed, upload_speed)
                
            #Guardar periódicamente
            if random.random() < 0.1:  # Guardar ~cada 50 ciclos
                self.save_data_history()
                
            prev_stats = current_stats
            prev_time = current_time

    def disconnect_network(self, icon=None, item=None):
        try:
            subprocess.run(['nmcli', 'networking', 'off'], check=True)
            self.send_notification(
                "Red Desconectada",
                "Se ha desconectado la red debido al exceso de consumo de datos"
            )
        except Exception as e:
            print(f"Error desconectando red: {e}")
            self.send_notification(
                "Error al Desconectar",
                "No se pudo desconectar la red automáticamente. Por favor, hazlo manualmente."
            )

    def reconnect_network(self, icon=None, item=None):
        try:
            subprocess.run(['nmcli', 'networking', 'on'], check=True)
        except Exception as e:
            print(f"Error reconectando red: {e}")

    """def reset_data_counters(self, reset_all=False):
        #Resetear contadores y guardar en historial
        current_month = datetime.now().strftime("%Y-%m")
    
        # Guardar mes anterior en historial si es necesario
        if self.data_history["current_month"] != current_month and self.data_history["current_month"]:
            month_key = self.data_history["current_month"]
            self.data_history["monthly_stats"][month_key] = {
                "downloaded": self.data_history["total_downloaded"],
                "uploaded": self.data_history["total_uploaded"]
            }
        
        if not reset_all:
            # Guardar mes anterior
            if self.data_history["current_month"]:
                self.data_history["monthly_stats"][self.data_history["current_month"]] = {
                    "downloaded": self.data_history["total_downloaded"],
                    "uploaded": self.data_history["total_uploaded"]
                }
        else:
            # Reiniciar todo
            self.data_history["monthly_stats"] = {}
    
        
        # Resetear contadores actuales
        
        self.data_history["current_month"] = current_month
        self.data_history["total_downloaded"] = 0
        self.data_history["total_uploaded"] = 0
        
        # Resetear contadores actuales
        if reset_all:
            self.data_history["monthly_stats"] = {}
            self.data_history["total_downloaded"] = 0
            self.data_history["total_uploaded"] = 0
        else:
            self.data_history["total_downloaded"] = 0
            self.data_history["total_uploaded"] = 0
    
        # Actualizar mes actual
        self.data_history["current_month"] = current_month
    
    
        # Guardar cambios
        self.save_data_history()
        
        # Actualizar estado local
        self.total_downloaded = 0
        self.total_uploaded = 0
        self.threshold_exceeded = False
        self.last_data_reset = datetime.now()
        
        if self.config['notifications']:
            self.send_notification(
                "Contadores de Datos Reseteados",
                "El consumo de datos ha sido reiniciado"
            )
        
        if self.gui_window:
            GLib.idle_add(self.update_gui)"""
    
    def reset_data_counters(self, reset_all=False):
        current_month = datetime.now().strftime("%Y-%m")

        if self.data_history["current_month"]:
            old_month = self.data_history["current_month"]
            self.data_history["monthly_stats"][old_month] = {
                "downloaded": float(self.data_history["total_downloaded"]),
                "uploaded": float(self.data_history["total_uploaded"])
            }

        if reset_all:
            self.data_history["monthly_stats"] = {}

        self.data_history["current_month"] = current_month
        self.data_history["total_downloaded"] = 0
        self.data_history["total_uploaded"] = 0
        self.save_data_history()

        self.total_downloaded = 0
        self.total_uploaded = 0
        self.threshold_exceeded = False
        self.last_data_reset = datetime.now()
        self.send_notification("Contadores Reiniciados", "Los contadores de consumo han sido reiniciados.")
    
    def update_connection_status(self, connected):
        if connected != self.connected:
            first_run = self.connected is None
            self.connected = connected
            self.blink_active = connected
            
            event = {
                'timestamp': datetime.now().isoformat(),
                'status': 'connected' if connected else 'disconnected'
            }
            self.connection_history.append(event)
            
            if len(self.connection_history) > 100:
                self.connection_history.pop(0)
            
            status = "conectado" if connected else "desconectado"
            
            if not first_run:
                self.send_notification(
                    f"Estado de red: {status}",
                    f"Tu conexión a Internet está {status}"
                )
            
            if not connected and self.icon:
                self.icon.icon = self.disconnected_image
            
            if self.gui_window:
                GLib.idle_add(self.update_gui)

    def blink_icon(self):
        while self.running:
            if self.blink_active and self.icon:
                self.blink_state = not self.blink_state
                if self.blink_state:
                    if self.check_vpn():
                        self.icon.icon = self.vpn_image
                    else:
                        self.icon.icon = self.connected_image
                else:
                    self.icon.icon = self.blink_off_image
            time.sleep(self.config['blink_interval'])

    def monitor_connection(self):
        failure_count = 0
        while self.running:
            connected = self.check_internet()
            self.update_connection_status(connected)
            
            if not connected:
                failure_count += 1
                if failure_count >= self.config['auto_restart_threshold']:
                    self.try_repair_network()
                    failure_count = 0
            else:
                failure_count = 0
                
            time.sleep(self.config['check_interval'])

    def try_repair_network(self, icon=None, item=None):
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True)
            self.send_notification(
                "Reparación de Red",
                "Se ha intentado reiniciar el servicio de red"
            )
        except:
            pass

    def start_system_tray(self):
        """Iniciar ícono en el panel del sistema con menú contextual"""
        # Crear ítem de consumo de datos
        #self.data_usage_menu_item = pystray.MenuItem('', lambda: None)
        
        menu_items = [
            pystray.MenuItem('Mostrar Panel de Control', self.show_gui),
            pystray.MenuItem('Consumo de Datos', self.show_data_usage_info),
            #pystray.MenuItem('Realizar Test de Velocidad', self.run_speed_test_now),
            pystray.MenuItem('Historial de Conexión', self.show_history_gui),
            #pystray.MenuItem('Preferencias', self.show_settings_gui),
            #pystray.MenuItem('Reparar Red', self.try_repair_network),
            pystray.MenuItem('Reconectar Red', self.reconnect_network),
            pystray.MenuItem('Salir', self.exit_app)
        ]
        
        self.icon = pystray.Icon(
            'net_monitor',
            icon=self.disconnected_image,
            title="Monitor de Internet",
            menu=pystray.Menu(*menu_items)
        )
        
        self.update_data_usage_menu()
        
        if self.config.get('show_gui_on_start', False):
            self.show_gui()
            
        self.icon.run()
    
    def get_data_usage_color(self, percentage):
        """Devuelve el color codificado según el porcentaje de consumo"""
        if percentage < 40:
            return self.DATA_CONSUMPTION_INDICATOR['green']
        elif 40 <= percentage < 80:
            return self.DATA_CONSUMPTION_INDICATOR['yellow']
        else:
            self.DATA_CONSUMPTION_INDICATOR['red']
    
    def show_settings_gui(self, icon=None, item=None):
        dialog = Gtk.Dialog(title="Preferencias", parent=self.gui_window, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Aplicar tamaño reducido a los botones
        for button in dialog.get_widget_for_response(Gtk.ResponseType.CANCEL), dialog.get_widget_for_response(Gtk.ResponseType.OK):
            button.set_size_request(60, 24)
            #button.get_child().set_property("font", "10")
        
        dialog.set_default_size(400, 300)
        
        content_area = dialog.get_content_area()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        content_area.add(box)
        
        # Sección de tema
        theme_frame = Gtk.Frame(label="Apariencia")
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=8)
        theme_frame.add(theme_box)
        box.pack_start(theme_frame, False, False, 0)
        
        # Modo oscuro
        dark_mode_box = Gtk.Box(spacing=6)
        self.dark_mode_switch = Gtk.Switch()
        self.dark_mode_switch.set_active(self.config.get('dark_mode', False))
        dark_mode_box.pack_start(Gtk.Label(label="Modo Oscuro"), False, False, 0)
        dark_mode_box.pack_end(self.dark_mode_switch, False, False, 0)
        theme_box.pack_start(dark_mode_box, False, False, 0)
        
        # Selector de color
        color_box = Gtk.Box(spacing=6)
        color_label = Gtk.Label(label="Color Principal:")
        self.color_button = Gtk.ColorButton()
        #self.color_button.set_rgba(Gdk.RGBA.parse(self.config.get('theme_color', PRIMARY_COLOR)))
        color_box.pack_start(color_label, False, False, 0)
        color_box.pack_end(self.color_button, False, False, 0)
        theme_box.pack_start(color_box, False, False, 0)
        
        # Sección de notificaciones
        notif_frame = Gtk.Frame(label="Notificaciones")
        notif_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=8)
        notif_frame.add(notif_box)
        box.pack_start(notif_frame, False, False, 0)

        # Contenedor horizontal para el interruptor y la etiqueta
        notif_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        notif_box.pack_start(notif_switch_box, False, False, 0)

        # Etiqueta y switch dentro del contenedor horizontal
        self.notif_switch = Gtk.Switch()
        self.notif_switch.set_active(self.config['notifications'])
        notif_switch_box.pack_start(Gtk.Label(label="Mostrar Notificaciones"), False, False, 0)
        notif_switch_box.pack_end(self.notif_switch, False, False, 0)
        
        # Sección de conexiones
        conn_frame = Gtk.Frame(label="Conexiones")
        conn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=8)
        conn_frame.add(conn_box)
        box.pack_start(conn_frame, False, False, 0)
        
        # Intervalo de verificación
        interval_box = Gtk.Box(spacing=6)
        interval_label = Gtk.Label(label="Intervalo de Verificación (seg):")
        self.interval_entry = Gtk.Entry()
        self.interval_entry.set_text(str(self.config['check_interval']))
        interval_box.pack_start(interval_label, False, False, 0)
        interval_box.pack_end(self.interval_entry, False, False, 0)
        conn_box.pack_start(interval_box, False, False, 0)
        
        # Umbral de velocidad baja
        speed_box = Gtk.Box(spacing=6)
        speed_label = Gtk.Label(label="Umbral de Velocidad Baja (Mbps):")
        self.speed_entry = Gtk.Entry()
        self.speed_entry.set_text(str(self.config['low_speed_threshold']))
        speed_box.pack_start(speed_label, False, False, 0)
        speed_box.pack_end(self.speed_entry, False, False, 0)
        conn_box.pack_start(speed_box, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            try:
                # Actualizar configuración
                self.config['dark_mode'] = self.dark_mode_switch.get_active()
                
                self.config['theme_color'] = self._color_to_hex(self.color_button.get_rgba())
                self.config['notifications'] = self.notif_switch.get_active()
                # Aplicar nuevos estilos
                ModernStyleProvider.apply_styles(self.config['dark_mode'])
                
                check_interval = int(self.interval_entry.get_text())
                if check_interval >= 1:
                    self.config['check_interval'] = check_interval
                    
                low_speed = float(self.speed_entry.get_text())
                if low_speed > 0:
                    self.config['low_speed_threshold'] = low_speed
                
                  
                self.save_config()
                
                
                
                if self.gui_window:
                    GLib.idle_add(self.update_gui)
                    
            except ValueError:
                pass
                
        dialog.destroy()

    def _color_to_hex(self, color):
        """Convertir color RGBA a hexadecimal"""
        return "#{:02x}{:02x}{:02x}".format(
            int(color.red * 255),
            int(color.green * 255),
            int(color.blue * 255)
        )

    def show_gui(self, icon=None, item=None):
        if self.gui_window:
            self.gui_window.present()
            return
            
        self.gui_window = Gtk.Window(title="Monitor de Internet")
        self.gui_window.set_default_size(800, 550)
        ModernStyleProvider.apply_styles  # Aplicar estilo personalizado
        self.gui_window.set_border_width(10)
        self.gui_window.connect("destroy", self.on_gui_close)
        
        if self.dark_mode:
            self.gui_window.get_style_context().add_class("dark-mode")
        
        if self.window_icon:
            self.gui_window.set_icon(self.window_icon)
            
        # Crear header bar personalizado
        header_bar = Gtk.HeaderBar()
        header_bar.set_title("Monitor de Internet")
        header_bar.set_show_close_button(True)
        header_bar.get_style_context().add_class("header-bar")
    
        # Botón de configuración más pequeño
        settings_button = Gtk.Button()
        settings_button.set_image(Gtk.Image.new_from_icon_name("preferences-system", Gtk.IconSize.MENU))
        settings_button.set_tooltip_text("Preferencias")
        settings_button.connect("clicked", self.show_settings_gui)
        settings_button.get_style_context().add_class("image-button")
        settings_button.set_size_request(24, 24)
    
        header_bar.pack_end(settings_button)
        self.gui_window.set_titlebar(header_bar)
        
        
        # Contenedor principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.gui_window.add(main_box)
        
        # Notebook para pestañas
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.LEFT)
        main_box.pack_start(notebook, True, True, 0)
        #self.update_app_usage_page()  # Cargar datos iniciales
        
        # Pestaña de estado
        status_page = self.create_status_page()
        notebook.append_page(status_page, Gtk.Image.new_from_icon_name("network-wireless", Gtk.IconSize.MENU))
        
        # Pestaña de historial
        history_page = self.create_history_page()
        notebook.append_page(history_page, Gtk.Image.new_from_icon_name("document-open-recent", Gtk.IconSize.MENU))
        
        # Pestaña de historial de Datos
        #history_datos_page = self.create_history_datos_page()
        #notebook.append_page(history_datos_page, Gtk.Image.new_from_icon_name("document-open-recent", Gtk.IconSize.MENU))
        
        # Pestaña de estadísticas
        stats_page = self.create_stats_page()
        notebook.append_page(stats_page, Gtk.Image.new_from_icon_name("system-run", Gtk.IconSize.MENU))
        
        # Pestaña de consumo por aplicación
        app_usage_page = self.create_app_usage_page()
        notebook.append_page(app_usage_page, Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.MENU))
        
        # Pestaña de estadísticas mensuales
        monthly_page = self.create_monthly_stats_page()
        bar_icon = get_bar_chart_icon_pixbuf(color="#1E88E5")  # Color primario o el que quieras
        #notebook.append_page(monthly_page, Gtk.Image.new_from_icon_name("office-chart-line", Gtk.IconSize.MENU))
        #notebook.append_page(monthly_page, Gtk.Image.new_from_pixbuf(bar_icon))
        notebook.append_page(monthly_page, Gtk.Image.new_from_icon_name("folder-download", Gtk.IconSize.MENU))
        notebook.connect("switch-page", self.on_monthly_page_shown)
        
        # Pestaña de Acerca de
        about_page = self.create_about_page()
        notebook.append_page(about_page, Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.MENU))
        
        # Mostrar ventana
        self.gui_window.show_all()
        self.update_gui()
        self.gui_update_id = GLib.timeout_add_seconds(2, self.update_gui)

    def create_status_page(self):
        """Crear página de estado con diseño moderno"""
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        
        # Tarjeta de estado general
        status_card = Gtk.Frame()
        status_card.get_style_context().add_class("card")
        status_grid = Gtk.Grid(column_spacing=20, row_spacing=10)
        status_grid.set_margin_top(10)
        status_grid.set_margin_bottom(10)
        status_grid.set_margin_start(10)
        status_grid.set_margin_end(10)
        status_card.add(status_grid)
        content.pack_start(status_card, False, False, 0)
        
        # Estado de conexión
        self.status_label = Gtk.Label()
        self.status_label.get_style_context().add_class("status-label")
        status_grid.attach(self.status_label, 0, 0, 1, 1)
        
        # Estado de VPN
        self.vpn_label = Gtk.Label()
        self.vpn_label.get_style_context().add_class("status-label")
        status_grid.attach(self.vpn_label, 1, 0, 1, 1)
        
        # Tiempo activo
        self.uptime_label = Gtk.Label()
        self.uptime_label.get_style_context().add_class("status-label")
        status_grid.attach(self.uptime_label, 0, 1, 2, 1)
        
        # Botones de acción rápida
        action_box = Gtk.Box(spacing=10)
        action_box.set_halign(Gtk.Align.CENTER)
        content.pack_start(action_box, False, False, 0)
        
        self.test_button = Gtk.Button(label="Realizar Test de Velocidad")
        self.test_button.connect("clicked", self.run_speed_test_now)
        self.test_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(self.test_button, False, False, 0)
        
        repair_button = Gtk.Button(label="Reparar Red")
        repair_button.connect("clicked", self.try_repair_network)
        repair_button.get_style_context().add_class("destructive-action")
        action_box.pack_start(repair_button, False, False, 0)
        
        # Tarjeta de velocidad
        speed_card = Gtk.Frame(label="Velocidad de Internet")
        speed_card.get_style_context().add_class("card")
        speed_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        speed_box.set_margin_top(10)
        speed_box.set_margin_bottom(10)
        speed_box.set_margin_start(10)
        speed_box.set_margin_end(10)
        speed_card.add(speed_box)
        content.pack_start(speed_card, False, False, 0)
        
        # Velocidad actual
        speed_grid = Gtk.Grid(column_spacing=40, row_spacing=10)
        speed_box.pack_start(speed_grid, False, False, 0)
        
        self.download_label = Gtk.Label()
        self.download_label.get_style_context().add_class("value-label")
        speed_grid.attach(self.download_label, 0, 0, 1, 1)
        
        self.upload_label = Gtk.Label()
        self.upload_label.get_style_context().add_class("value-label")
        speed_grid.attach(self.upload_label, 1, 0, 1, 1)
        
        self.ping_label = Gtk.Label()
        self.ping_label.get_style_context().add_class("value-label")
        speed_grid.attach(self.ping_label, 2, 0, 1, 1)
        
        # Información adicional
        info_grid = Gtk.Grid(column_spacing=20, row_spacing=5)
        speed_box.pack_start(info_grid, False, False, 0)
        
        self.last_test_label = Gtk.Label()
        info_grid.attach(Gtk.Label(label="Último test:"), 0, 0, 1, 1)
        info_grid.attach(self.last_test_label, 1, 0, 1, 1)
        
        return scrolled

    def create_stats_page(self):
        """Crear página de estadísticas con diseño moderno"""
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        
        # Tarjeta de consumo de datos
        data_card = Gtk.Frame(label="Consumo de Datos")
        data_card.get_style_context().add_class("card")
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        data_box.set_margin_top(10)
        data_box.set_margin_bottom(10)
        data_box.set_margin_start(10)
        data_box.set_margin_end(10)
        data_card.add(data_box)
        content.pack_start(data_card, False, False, 0)
        
        # Consumo actual
        data_grid = Gtk.Grid(column_spacing=40, row_spacing=10)
        data_box.pack_start(data_grid, False, False, 0)
        
        self.downloaded_label = Gtk.Label()
        self.downloaded_label.get_style_context().add_class("value-label")
        data_grid.attach(self.downloaded_label, 0, 0, 1, 1)
        
        self.uploaded_label = Gtk.Label()
        self.uploaded_label.get_style_context().add_class("value-label")
        data_grid.attach(self.uploaded_label, 1, 0, 1, 1)
        
        self.total_data_label = Gtk.Label()
        self.total_data_label.get_style_context().add_class("value-label")
        data_grid.attach(self.total_data_label, 2, 0, 1, 1)
        
        # Configuración de umbral
        threshold_box = Gtk.Box(spacing=10)
        data_box.pack_start(threshold_box, False, False, 0)
        
        threshold_box.pack_start(Gtk.Label(label="Umbral:"), False, False, 0)
        self.threshold_label = Gtk.Label()
        threshold_box.pack_start(self.threshold_label, False, False, 0)
        
        # Botones de acción
        action_box = Gtk.Box(spacing=10)
        data_box.pack_start(action_box, False, False, 0)
        
        reset_button = Gtk.Button(label="Resetear Contadores")
        reset_button.connect("clicked", lambda b: self.reset_data_counters())
        reset_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(reset_button, False, False, 0)
        
        config_button = Gtk.Button(label="Cambiar Umbral")
        config_button.connect("clicked", self.show_threshold_dialog)
        config_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(config_button, False, False, 0)
        
        """config_button = Gtk.Button(label="Historial Consumo")
        config_button.connect("clicked", self.show_data_history_gui)
        config_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(config_button, False, False, 0)"""
        
        
        # Switch de desconexión automática
        disconnect_box = Gtk.Box(spacing=10)
        data_box.pack_start(disconnect_box, False, False, 0)
        
        self.disconnect_switch = Gtk.Switch()
        self.disconnect_switch.set_active(self.config['auto_disconnect'])
        self.disconnect_switch.connect("state-set", self.toggle_auto_disconnect)
        disconnect_box.pack_start(Gtk.Label(label="Desconectar al exceder umbral:"), False, False, 0)
        disconnect_box.pack_start(self.disconnect_switch, False, False, 0)
        
        # Tarjeta de uso en tiempo real
        usage_card = Gtk.Frame(label="Uso de Red en Tiempo Real")
        usage_card.get_style_context().add_class("card")
        usage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        usage_box.set_margin_top(10)
        usage_box.set_margin_bottom(10)
        usage_box.set_margin_start(10)
        usage_box.set_margin_end(10)
        usage_card.add(usage_box)
        content.pack_start(usage_card, False, False, 0)
        
        self.download_usage_label = Gtk.Label()
        self.download_usage_label.get_style_context().add_class("status-label")
        usage_box.pack_start(self.download_usage_label, False, False, 0)
        
        self.upload_usage_label = Gtk.Label()
        self.upload_usage_label.get_style_context().add_class("status-label")
        usage_box.pack_start(self.upload_usage_label, False, False, 0)
        
        return scrolled
    
    #def create_about_page(self):
     #   pass
    
    def create_about_page(self):
        """Crear página de 'Acerca de' con información de la aplicación"""
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)

        # Tarjeta principal
        about_card = Gtk.Frame(label="Acerca de LNetMon")
        about_card.get_style_context().add_class("card")
        about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        about_box.set_margin_top(10)
        about_box.set_margin_bottom(10)
        about_box.set_margin_start(10)
        about_box.set_margin_end(10)
        about_card.add(about_box)
        content.pack_start(about_card, False, False, 0)

        # Logo/Icono
        #icon_image = Gtk.Image.new_from_pixbuf(get_info_icon_pixbuf(color=PRIMARY_COLOR))
        #icon_image.set_halign(Gtk.Align.CENTER)
        #about_box.pack_start(icon_image, False, False, 0)

        # Información principal
        info_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        about_box.pack_start(info_grid, False, False, 0)

        info_grid.attach(Gtk.Label(label="Nombre:"), 0, 0, 1, 1)
        info_grid.attach(Gtk.Label(label="<b>LNetMon</b>", use_markup=True), 1, 0, 1, 1)

        info_grid.attach(Gtk.Label(label="Versión:"), 0, 1, 1, 1)
        info_grid.attach(Gtk.Label(label="<b>0.1</b>", use_markup=True), 1, 1, 1, 1)

        info_grid.attach(Gtk.Label(label="Descripción:"), 0, 2, 1, 1)
        desc_label = Gtk.Label()
        desc_label.set_markup("Herramienta para monitorear conexión, velocidad, consumo de datos y estado de red.")
        desc_label.set_line_wrap(True)
        desc_label.set_justify(Gtk.Justification.FILL)
        desc_label.set_halign(Gtk.Align.START)
        info_grid.attach(desc_label, 1, 2, 1, 1)

        info_grid.attach(Gtk.Label(label="Autor(es):"), 0, 3, 1, 1)
        authors_label = Gtk.Label()
        authors_label.set_markup("Ing. Alejandro Miguel Blanco Arias")
        authors_label.set_halign(Gtk.Align.START)
        info_grid.attach(authors_label, 1, 3, 1, 1)

        info_grid.attach(Gtk.Label(label="Licencia:"), 0, 4, 1, 1)
        license_label = Gtk.Label()
        license_label.set_markup("GPLv3")
        license_label.set_halign(Gtk.Align.START)
        info_grid.attach(license_label, 1, 4, 1, 1)

        info_grid.attach(Gtk.Label(label="Sitio Web:"), 0, 5, 1, 1)
        web_label = Gtk.Label()
        web_label.set_markup('<a href="https://github.com/alexx181207/lnetmon">GitHub</a>') 
        web_label.set_halign(Gtk.Align.START)
        info_grid.attach(web_label, 1, 5, 1, 1)

        # Botón de créditos
        credits_button = Gtk.Button(label="Ver Créditos")
        credits_button.get_style_context().add_class("suggested-action")
        credits_button.connect("clicked", self.show_credits)
        about_box.pack_start(credits_button, False, False, 0)
        
        license_button = Gtk.Button(label="Ver Licencia")
        license_button.connect("clicked", self.show_license_dialog)
        about_box.pack_start(license_button, False, False, 0)
        
        update_button = Gtk.Button(label="Buscar Actualizaciones")
        update_button.connect("clicked", self.check_for_updates)
        about_box.pack_start(update_button, False, False, 0)

        return scrolled
    
    def show_credits(self, button):
        dialog = Gtk.MessageDialog(
            parent=self.gui_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Créditos",
        )
        dialog.format_secondary_markup("""
        <b>Desarrollado por:</b> Ing. Alejandro Miguel Blanco Arias\n
        <b>Colaboración especial:</b> Comunidad de Software libre de Novum\n
        <b>Librerías utilizadas:</b>\n
        - PyGObject (GTK 3)\n
        - speedtest-cli\n
        - psutil\n
        - Pillow\n
        - pystray\n
        - requests
        """)
        dialog.run()
        dialog.destroy()
    
    def create_history_page(self):
        """Crear página de historial con diseño moderno"""
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        
        # Tarjeta de historial
        history_card = Gtk.Frame(label="Historial de Conexión")
        history_card.get_style_context().add_class("card")
        content.pack_start(history_card, True, True, 0)
        
        # Contenedor de historial
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        history_box.set_margin_top(10)
        history_box.set_margin_bottom(10)
        history_box.set_margin_start(10)
        history_box.set_margin_end(10)
        history_card.add(history_box)
        
        # Lista de historial
        self.history_list = Gtk.ListStore(str, str)
        treeview = Gtk.TreeView(model=self.history_list)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Fecha", renderer, text=0)
        column.set_min_width(150)
        treeview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Estado", renderer, text=1)
        column.set_min_width(100)
        treeview.append_column(column)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(treeview)
        history_box.pack_start(scroll, True, True, 0)
        
        # Botón para exportar
        export_button = Gtk.Button(label="Exportar Historial")
        export_button.connect("clicked", self.export_history)
        export_button.get_style_context().add_class("suggested-action")
        history_box.pack_start(export_button, False, False, 0)
        
        return scrolled
    
    def create_history_datos_page(self):
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        
        # Tarjeta de historial
        #history_card = Gtk.Frame(label="Historial de Conexión")
        #history_card.get_style_context().add_class("card")
        #content.pack_start(history_card, True, True, 0)
        

        # Tarjeta de historial
        history_card = Gtk.Frame(label="Historial de Consumo Mensual")
        history_card.get_style_context().add_class("card")
        content.pack_start(history_card, True, True, 0)

        #Contenedor de Historial de Consumo de Datos
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        history_box.set_margin_top(10)
        history_box.set_margin_bottom(10)
        history_box.set_margin_start(10)
        history_box.set_margin_end(10)
        history_card.add(history_box)
        
        
        # Lista de historial
        self.history_data_list = Gtk.ListStore(str, str, str, str, str)  # Mes, Descargado, Subido, Total, %
        treeview = Gtk.TreeView(model=self.history_data_list)

        for i, title in enumerate(["Mes", "Descargado (MB)", "Subido (MB)", "Total (MB)", "Por ciento"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            treeview.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        history_box.pack_start(scroll, True, True, 0)

        # Botón exportar
        export_button = Gtk.Button(label="Exportar Historial")
        export_button.connect("clicked", self.export_data_history)
        export_button.get_style_context().add_class("suggested-action")
        history_box.pack_start(export_button, False, False, 0)

        return scrolled
    
    def export_history(self, button):
        """Exportar historial a archivo CSV"""
        dialog = Gtk.FileChooserDialog(
            title="Guardar Historial",
            parent=self.gui_window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        dialog.set_current_name("historial_conexion.csv")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                with open(filename, 'w') as f:
                    f.write("Fecha,Hora,Estado\n")
                    for event in self.connection_history:
                        dt = datetime.fromisoformat(event['timestamp'])
                        status = "Conectado" if event['status'] == 'connected' else "Desconectado"
                        f.write(f"{dt.strftime('%Y-%m-%d,%H:%M:%S')},{status}\n")
            except Exception as e:
                self.show_error_dialog(f"No se pudo guardar el archivo: {e}")
                
        dialog.destroy()

    def show_error_dialog(self, message):
        """Mostrar diálogo de error"""
        dialog = Gtk.MessageDialog(
            parent=self.gui_window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def toggle_auto_disconnect(self, switch, state):
        """Activar/desactivar desconexión automática"""
        self.config['auto_disconnect'] = state
        self.save_config()

    def show_threshold_dialog(self, widget):
        #Mostrar diálogo para cambiar el umbral de  y ver historial
        dialog = Gtk.Dialog(title="Configuración de consumo", parent=self.gui_window, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(300, 150)
        
        content_area = dialog.get_content_area()
        notebook = Gtk.Notebook()
        content_area.add(notebook)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        content_area.add(box)
        
        # Pestaña de configuración
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        notebook.append_page(config_box, Gtk.Label(label="Configuración"))
        
        label = Gtk.Label(label="Ingrese el nuevo umbral de consumo de datos (MB):")
        box.pack_start(label, False, False, 0)
        
        entry = Gtk.Entry()
        entry.set_text(str(self.data_threshold))
        entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        box.pack_start(entry, False, False, 0)
        
         # Umbral actual
        threshold_box = Gtk.Box(spacing=10)
        threshold_label = Gtk.Label(label="Umbral mensual (MB):")
        threshold_entry = Gtk.Entry()
        threshold_entry.set_text(str(self.data_threshold))
        threshold_box.pack_start(threshold_label, False, False, 0)
        threshold_box.pack_start(threshold_entry, True, True, 0)
        config_box.pack_start(threshold_box, False, False, 0)
    
        # Pestaña de historialCambiar
        #history_page = self.create_data_history_page()
        #notebook.append_page(history_page, Gtk.Label(label="Historial"))
    
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            try:
                new_threshold = float(entry.get_text())
                if new_threshold > 0:
                    self.data_threshold = new_threshold
                    self.config['data_threshold'] = new_threshold
                    self.save_config()
                    self.threshold_exceeded = False
                    if self.gui_window:
                        GLib.idle_add(self.update_gui)
            except ValueError:
                pass
                
        dialog.destroy()
    
    """def show_threshold_dialog(self, widget):
        dialog = Gtk.Dialog(title="Configurar Umbral de Datos", parent=self.gui_window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_default_size(300, 150)

        notebook = Gtk.Notebook()
        dialog.get_content_area().add(notebook)

        # Pestaña de configuración
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        notebook.append_page(config_box, Gtk.Label(label="Umbral"))

        threshold_box = Gtk.Box(spacing=10)
        threshold_label = Gtk.Label(label="Umbral mensual (MB):")
        self.threshold_entry = Gtk.Entry()
        self.threshold_entry.set_text(str(self.data_threshold))
        threshold_box.pack_start(threshold_label, False, False, 0)
        threshold_box.pack_start(self.threshold_entry, True, True, 0)
        config_box.pack_start(threshold_box, False, False, 0)

        # Pestaña de historial
        history_page = self.create_data_history_page()
        notebook.append_page(history_page, Gtk.Label(label="Historial"))

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            try:
                new_threshold = float(self.threshold_entry.get_text())
                if new_threshold > 0:
                    self.data_threshold = new_threshold
                    self.config['data_threshold'] = new_threshold
                    self.save_config()
                    self.threshold_exceeded = False
                    GLib.idle_add(self.update_gui)
            except ValueError:
                pass

        dialog.destroy()"""
    
    def update_network_usage(self, download_speed, upload_speed):
        """Actualizar el uso de red en tiempo real"""
        if not self.gui_window:
            return
            
        self.download_usage_label.set_text(f"Descarga: {download_speed:.2f} KB/s")
        self.upload_usage_label.set_text(f"Subida: {upload_speed:.2f} KB/s")
    
    def show_data_usage_info(self, icon, item):
        total_data = self.total_downloaded + self.total_uploaded
        percentage = (total_data / self.data_threshold) * 100 if self.data_threshold > 0 else 0
    
        # Mostrar mensaje de notificación o ventana emergente
        message = f"Consumo: {total_data:.1f}/{self.data_threshold} MB\n"
        message += f"({percentage:.0f}% del umbral)\n"
    
        if percentage < 40:
            message += "Estado: ✅ Bajo consumo"
        elif 40 <= percentage < 80:
            message += "Estado: ⚠️ Consumo moderado"
        else:
            message += "Estado: ❗ Consumo excedido"
    
        self.icon.notify(message, title="Consumo de Datos")
    
    def update_data_usage_menu(self):
        """Actualizar el ítem del menú con información de consumo de datos"""
        total_data = self.total_downloaded + self.total_uploaded
        percentage = (total_data / self.data_threshold) * 100 if self.data_threshold > 0 else 0
    
        # Determinar color según porcentaje
        #color_indicator = self.get_data_usage_color(percentage)
        
        #status = "🟢" if percentage < 40 else "🟡" if percentage < 80 else "🔴"
        
        # Determinar color según porcentaje
        if percentage < 40:
            status = "🟢"  # Verde
        elif 40 <= percentage < 80:
            status = "🟡"  # Amarillo
        else:
            status = "🔴"  # Rojo

        # Formatear texto
        text = f"{status} Consumo: {total_data:.1f}/{self.data_threshold} MB ({percentage:.0f}%)"
        
        # Reconstruir el menú completo con el nuevo texto
        menu_items = [
            pystray.MenuItem('Mostrar Panel de Control', self.show_gui),
            pystray.MenuItem(text, lambda icon, item: None),  # Texto dinámico
            #pystray.MenuItem('Realizar Test de Velocidad', self.run_speed_test_now),
            pystray.MenuItem('Historial de Conexión', self.show_history_gui),
            #pystray.MenuItem('Preferencias', self.show_settings_gui),
            #pystray.MenuItem('Reparar Red', self.try_repair_network),
            pystray.MenuItem('Reconectar Red', self.reconnect_network),
            pystray.MenuItem('Salir', self.exit_app)
        ]
        
        # Actualizar el menú del ícono
        self.icon.menu = pystray.Menu(*menu_items)
        self.icon.update_menu()
    
        # Actualizar el ítem del menú
        """if self.data_usage_menu_item:
            self.data_usage_menu_item.text = text
            if self.icon:
                self.icon.update_menu()"""
    
    def update_gui(self):
        """Actualizar los datos en la interfaz gráfica"""
        if not self.gui_window:
            return False
            
        # Estado de conexión
        status = "Conectado" if self.connected else "Desconectado"
        status_color = "green" if self.connected else "red"
        self.status_label.set_markup(f"Estado: <b><span color='{status_color}'>{status}</span></b>")
        
        # Estado VPN
        vpn_status = "Detectada" if self.vpn_active else "No detectada"
        vpn_color = "blue" if self.vpn_active else "gray"
        self.vpn_label.set_markup(f"VPN: <b><span color='{vpn_color}'>{vpn_status}</span></b>")
        
        # Tiempo activo
        if self.connection_history:
            uptime_percent = self.calculate_uptime_percentage()
            self.uptime_label.set_markup(f"<b>Tiempo activo:</b> {uptime_percent:.2f}%")
        
        # Velocidad de internet
        if not self.speed_test_in_progress:
            if self.speed_results:
                self.download_label.set_markup(f"<big><b>↓ {self.speed_results['download']:.2f} Mbps</b></big>")
                self.upload_label.set_markup(f"<big><b>↑ {self.speed_results['upload']:.2f} Mbps</b></big>")
                self.ping_label.set_markup(f"<big><b>• {self.speed_results['ping']:.2f} ms</b></big>")
                
                if self.last_speed_test:
                    last_test_str = self.last_speed_test.strftime("%Y-%m-%d %H:%M:%S")
                    self.last_test_label.set_text(f"Último test: {last_test_str}")
                    
            self.test_button.set_sensitive(True)
        else:
            self.download_label.set_markup("<big><b>Realizando test...</b></big>")
            self.upload_label.set_text("Por favor espera")
            self.ping_label.set_text("")
            self.last_test_label.set_text(f"Último test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Consumo de datos
        self.downloaded_label.set_markup(f"<big><b>↓ {self.total_downloaded:.2f} MB</b></big>")
        self.uploaded_label.set_markup(f"<big><b>↑ {self.total_uploaded:.2f} MB</b></big>")
        total_data = self.total_downloaded + self.total_uploaded
        #if total_data >= self.data_threshold:
         #   self.total_data_label.set_markup(f"<span color='red'><big><b>Σ {total_data:.2f} MB</b></big></span>")
        #else:
         #   self.total_data_label.set_markup(f"<big><b>Σ {total_data:.2f} MB</b></big>")
        
        # Por esta:
        percentage = (total_data / self.data_threshold) * 100 if self.data_threshold > 0 else 0
        if percentage < 40:
            self.total_data_label.set_markup(f"<b>{total_data:.2f} MB</b> ({percentage:.0f}%)")
        elif 40 <= percentage < 80:
            self.total_data_label.set_markup(f"<span color='orange'><b>{total_data:.2f} MB</b></span> ({percentage:.0f}%)")
        else:
            self.total_data_label.set_markup(f"<span color='red'><b>{total_data:.2f} MB</b></span> ({percentage:.0f}%)")    
        self.threshold_label.set_text(f"{self.data_threshold} MB")
        
        """# Mostrar consumo total
        total_data = self.total_downloaded + self.total_uploaded
        if total_data >= self.data_threshold:
            self.total_data_label.set_markup(f"<span color='red'><b>{total_data:.2f} MB</b></span>")
        else:
            self.total_data_label.set_text(f"{total_data:.2f} MB")"""
    
        """# Mostrar consumo mensual (total del mes actual)
        month_data = self.data_history.get("monthly_stats", {}).get(self.data_history["current_month"], None)
        if month_data:
            total_month = month_data["downloaded"] + month_data["uploaded"]
            self.month_data_label.set_markup(f"{total_month:.2f} MB (mes)")
        else:
            self.month_data_label.set_markup("-- MB")"""
            
        # Actualizar menú de sistema tray
        self.update_data_usage_menu()
        
        #Actualizar los consumos por aplicación
        self.update_app_usage_page()
    
        # Historial reciente
        self.history_list.clear()
        for event in self.connection_history:
            dt = datetime.fromisoformat(event['timestamp'])
            status = "Conectado" if event['status'] == 'connected' else "Desconectado"
            self.history_list.append([dt.strftime("%Y-%m-%d %H:%M:%S"), status])
            
            
        """# Historial Datos reciente
        self.history_data_list.clear()
        for event in self.connection_history:
            dt = datetime.fromisoformat(event['timestamp'])
            status = "Conectado" if event['status'] == 'connected' else "Desconectado"
            self.history_data_list.append([dt.strftime("%Y-%m-%d %H:%M:%S"), status])
         """
        
        # Actualizar historial en GUI si está abierto
        if hasattr(self, "data_history_window"):
            self.update_data_history_page()
              
        return True

    def calculate_uptime_percentage(self):
        """Calcular porcentaje de tiempo de actividad"""
        if not self.connection_history:
            return 0.0
            
        connected_time = 0
        first_time = datetime.fromisoformat(self.connection_history[0]['timestamp'])
        last_time = datetime.fromisoformat(self.connection_history[-1]['timestamp'])
        total_time = (datetime.now() - first_time).total_seconds()
        
        for i in range(len(self.connection_history) - 1):
            if self.connection_history[i]['status'] == 'connected':
                start = datetime.fromisoformat(self.connection_history[i]['timestamp'])
                end = datetime.fromisoformat(self.connection_history[i+1]['timestamp'])
                connected_time += (end - start).total_seconds()
                
        if self.connection_history[-1]['status'] == 'connected':
            start = datetime.fromisoformat(self.connection_history[-1]['timestamp'])
            connected_time += (datetime.now() - start).total_seconds()
            
        return (connected_time / total_time) * 100 if total_time > 0 else 100.0
    
    def check_monthly_reset(self):
        """Verificar si hay que reiniciar contadores mensuales"""
        current_month = datetime.now().strftime("%Y-%m")
    
        if self.data_history["current_month"] != current_month:
            # Guardar mes anterior
            old_month = self.data_history["current_month"]
            if old_month:
                self.data_history["monthly_stats"][old_month] = {
                    "downloaded": self.data_history["total_downloaded"],
                    "uploaded": self.data_history["total_uploaded"]
                }
        
            # Reiniciar contadores
            self.data_history["current_month"] = current_month
            self.data_history["total_downloaded"] = 0
            self.data_history["total_uploaded"] = 0
            self.save_data_history()
            
            # Actualizar estado local
            self.total_downloaded = 0
            self.total_uploaded = 0
            self.threshold_exceeded = False
            self.last_data_reset = datetime.now()
        
        
            # Actualizar GUI
            if self.gui_window:
                GLib.idle_add(self.update_gui)
    
    def periodic_data_check(self):
        """Verificar rotación de meses y otros datos"""
        while self.running:
            self.check_monthly_reset()
            time.sleep(86400)  # Verificar una vez al día
    
    def show_history_gui(self, icon=None, item=None):
        """Mostrar ventana de historial completo"""
        history_window = Gtk.Window(title="Historial Completo de Conexión")
        history_window.set_default_size(400, 500)
        history_window.set_border_width(10)
        
        # Crear lista de historial
        history_list = Gtk.ListStore(str, str)  # Fecha, Estado
        treeview = Gtk.TreeView(model=history_list)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Fecha", renderer, text=0)
        column.set_min_width(150)
        treeview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Estado", renderer, text=1)
        column.set_min_width(100)
        treeview.append_column(column)
        
        # Llenar con datos
        for event in self.connection_history:
            dt = datetime.fromisoformat(event['timestamp'])
            status = "Conectado" if event['status'] == 'connected' else "Desconectado"
            history_list.append([dt.strftime("%Y-%m-%d %H:%M:%S"), status])
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(treeview)
        
        history_window.add(scroll)
        history_window.show_all()
    
    """def show_data_history_gui(self, icon=None, item=None):
        #Mostrar historial de consumo mensual
        history_window = Gtk.Window(title="Historial de Consumo")
        history_window.set_default_size(400, 300)
        history_window.set_border_width(10)
    
        # Crear modelo de lista
        history_list = Gtk.ListStore(str, str, str)  # Mes, Descarga, Subida
        treeview = Gtk.TreeView(model=history_list)
    
        # Columnas
        for i, title in enumerate(["Mes", "Descargado (MB)", "Subido (MB)"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            treeview.append_column(column)
    
        # Llenar datos
        for month, data in sorted(self.data_history["monthly_stats"].items(), reverse=True):
            history_list.append([
                month,
                f"{data['downloaded']:.2f}",
                f"{data['uploaded']:.2f}"
            ])
    
        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        history_window.add(scroll)
        history_window.show_all()"""
    
    def load_data_history(self):
        """Cargar historial de consumo desde archivo"""
        data_file = os.path.expanduser("~/.config/internet-monitor/data_history.json")
        default_data = {
            "current_month": datetime.now().strftime("%Y-%m"),
            "total_downloaded": 0,
            "total_uploaded": 0,
            "monthly_stats": {},
            "app_stats": {}
        }
        
        #if "app_stats" not in self.data_history:
         #   self.data_history["app_stats"] = {}

    
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    
                    # Validar campos obligatorios
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]
                
                    # Convertir strings a números
                    data["total_downloaded"] = float(data.get("total_downloaded", 0))
                    data["total_uploaded"] = float(data.get("total_uploaded", 0))
                    return data
            return default_data
        except Exception as e:
            print(f"Error cargando historial: {e}")
            return default_data

    def save_data_history(self):
        """Guardar historial de consumo en archivo"""
        data_file = os.path.expanduser("~/.config/internet-monitor/data_history.json")
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
    
        data = {
            "current_month": self.data_history["current_month"],
            "total_downloaded": self.data_history["total_downloaded"],
            "total_uploaded": self.data_history["total_uploaded"],
            "monthly_stats": self.data_history["monthly_stats"],
            "app_stats": self.data_history["app_stats"]
        }
        
        #data["app_stats"] = self.data_history["app_stats"]
    
        try:
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
        
            # Actualizar GUI si está abierta y la pestaña activa
            if self.gui_window and hasattr(self, 'monthly_model'):
                GLib.idle_add(self.populate_monthly_model)
            
        except Exception as e:
            print(f"Error guardando historial: {e}")
        
    """def create_data_history_page(self):
        #Crear página de historial de consumo
        scrolled = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        scrolled.add(box)
    
        # Tabla de historial
        history_list = Gtk.ListStore(str, str, str)  # Mes, Descarga, Subida
        treeview = Gtk.TreeView(model=history_list)
    
        # Columnas
        for i, title in enumerate(["Mes", "Descargado (MB)", "Subido (MB)"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            treeview.append_column(column)
    
        # Llenar datos
        for month, data in sorted(self.data_history["monthly_stats"].items(), reverse=True):
            self.history_data_list.append([
                month,
                f"{data['downloaded']:.2f}",
                f"{data['uploaded']:.2f}",
            ])
    
        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        box.pack_start(scroll, True, True, 0)
    
        # Botón de limpiar historial
        clear_button = Gtk.Button(label="Limpiar Historial")
        clear_button.connect("clicked", self.clear_data_history)
        box.pack_start(clear_button, False, False, 0)
    
        return scrolled"""
    
    
    def create_monthly_stats_page(self):
        """Crear página con historial de consumo mensual"""
        #scrolled = Gtk.ScrolledWindow()
        #content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        #scrolled.add(content)
        
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        
        # Tarjeta de historial
        history_card = Gtk.Frame(label="Historial de Consumo Mensual")
        history_card.get_style_context().add_class("card")
        content.pack_start(history_card, True, True, 0)

        #Contenedor de Historial de Consumo de Datos
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        history_box.set_margin_top(10)
        history_box.set_margin_bottom(10)
        history_box.set_margin_start(10)
        history_box.set_margin_end(10)
        history_card.add(history_box)
        
    
        # Crear modelo de datos (Mes, Descargado, Subido, Total)
        self.monthly_model = Gtk.ListStore(str, str, str, str)
        self.populate_monthly_model()  # Llenar con datos iniciales
    
        # Crear vista de lista
        treeview = Gtk.TreeView(model=self.monthly_model)
    
        # Definir columnas
        for i, title in enumerate(["Mes", "Descargado (MB)", "Subido (MB)", "Total (MB)"]):
            renderer = Gtk.CellRendererText()
            renderer.set_property("xalign", 0.5)  # Centrar texto
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_alignment(0.5)  # Alinear columna al centro
            column.set_sort_column_id(i)
            treeview.append_column(column)
            
        # En create_monthly_stats_page(), después de crear la columna "Total (MB)"
        #percent_column = Gtk.TreeViewColumn("Porcentaje", Gtk.CellRendererText(), text=4)
        #treeview.append_column(percent_column)  
    
        # Añadir barra de scroll
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(treeview)
        history_box.pack_start(scroll, True, True, 0)
        
        return scrolled
    
    def populate_monthly_model(self):
        """Llenar modelo con datos históricos mensuales"""
        self.monthly_model.clear()
    
        # Ordenar por mes (más reciente primero)
        stats = self.data_history.get("monthly_stats", {})
        for month in sorted(stats.keys(), reverse=True):
            data = stats[month]
            total = data["downloaded"] + data["uploaded"]
            #percent = (total / self.data_threshold) * 100
            self.monthly_model.append([
                month,
                f"{data['downloaded']:.2f}",
                f"{data['uploaded']:.2f}",
                f"{total:.2f}"
                #f"{percent:.1f}%"
            ])
            
    
    def on_monthly_page_shown(self, widget, page, page_num):
        """Actualizar datos cuando se cambia a la pestaña de estadísticas mensuales"""
        if page_num == 2:  # Cambiar según la posición de la pestaña
            self.populate_monthly_model()
    

    def get_app_data_usage(self):
        """Obtener consumo de datos por proceso"""
        usage = {}

        for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
            try:
                # Obtener nombre del proceso
                name = proc.info['name'] or f"Unknown-{proc.pid}"
            
                # Obtener contadores de E/S
                io = proc.info['io_counters']
                if io:
                    download = io.read_bytes / (8*1024*1024*1024) # MB
                    upload = io.write_bytes /  (8*1024*1024*1024)
                    total = download + upload

                    if name in usage:
                        usage[name]['download'] += download
                        usage[name]['upload'] += upload
                        usage[name]['total'] += total
                    else:
                        usage[name] = {
                            "download": round(download, 2),
                            "upload": round(upload, 2),
                            "total": round(total, 2)
                        }

            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                continue

        return usage

    def monitor_app_data(self):
        """Monitorear consumo de datos por aplicación"""
        while self.running:
            current_usage = self.get_app_data_usage()
        
            # Actualizar historial acumulativo
            for app, data in current_usage.items():
                if app not in self.data_history["app_stats"]:
                    self.data_history["app_stats"][app] = {"download": 0, "upload": 0, "total": 0}
            
                # Actualizar acumulados
                self.data_history["app_stats"][app]["download"] += data["download"]
                self.data_history["app_stats"][app]["upload"] += data["upload"]
                self.data_history["app_stats"][app]["total"] += data["total"]
        
            # Guardar periódicamente
            if random.random() < 0.1:
                self.save_data_history()
        
            time.sleep(self.config.get('check_interval', 5))
    
    """def create_app_usage_page(self):
        #Crear pestaña de consumo por aplicación
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled.add(content)

        # Tarjeta de consumo por aplicación
        app_card = Gtk.Frame(label="Consumo por Aplicación")
        app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        app_card.add(app_box)
        content.pack_start(app_card, True, True, 0)

        # Tabla de aplicaciones
        self.app_usage_list = Gtk.ListStore(str, float, float, float, str)  # Nombre, descarga, subida, total, porcentaje
        treeview = Gtk.TreeView(model=self.app_usage_list)
    
        # Definir columnas
        headers = ["Aplicación", "Descargado (MB)", "Subido (MB)", "Total (MB)", "Porcentaje (%)"]
        for i, title in enumerate(headers):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i if i == 0 else None, xalign=0.99 if i > 0 else 0.01)
            if i > 0:
                column.set_cell_data_func(renderer, lambda col, cell, model, it, idx: cell.set_property("xalign", 1.0) if idx > 0 else None)
            treeview.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        app_box.pack_start(scroll, True, True, 0)

        # Botón de reinicio
        reset_button = Gtk.Button(label="Reiniciar Contadores")
        reset_button.connect("clicked", self.reset_app_counters)
        reset_button.get_style_context().add_class("suggested-action")
        app_box.pack_start(reset_button, False, False, 0)

        return scrolled"""
    
    def create_app_usage_page(self):
        """Crear pestaña de consumo por aplicación"""
        scrolled = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.add(content)
        

        # Tarjeta de consumo por aplicación
        app_card = Gtk.Frame(label="Consumo por Aplicación")
        app_card.get_style_context().add_class("card")
        content.pack_start(app_card, True, True, 0)
        
        #Contenedor de Historial de Consumo de Datos por Aplicación
        app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        app_box.set_margin_top(10)
        app_box.set_margin_bottom(10)
        app_box.set_margin_start(10)
        app_box.set_margin_end(10)
        app_card.add(app_box)
        
        
        # Tabla de aplicaciones
        self.app_usage_list = Gtk.ListStore(str, str, str, str, str)  # Nombre, descarga, subida, total, porcentaje
        self.update_app_usage_page()
        treeview = Gtk.TreeView(model=self.app_usage_list)

        # Definir columnas
        headers = ["Aplicación", "Descargado (MB)", "Subido (MB)", "Total (MB)", "Porcentaje (%)"]
        for i, title in enumerate(headers):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
        
            # Alinear texto a la derecha para columnas numéricas
            if i > 0:
                renderer.set_property("xalign", 0.5)
                renderer.set_property("weight_set", True)
                #renderer.set_property("weight", Pango.Weight.BOLD)
        
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i)
            treeview.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        app_box.pack_start(scroll, True, True, 0)

        # Botón de reinicio
        reset_button = Gtk.Button(label="Reiniciar Contadores")
        reset_button.connect("clicked", self.reset_app_counters)
        reset_button.get_style_context().add_class("suggested-action")
        app_box.pack_start(reset_button, False, False, 0)

        return scrolled
    
    def reset_app_counters(self, button=None):
        """Resetear contadores de consumo por aplicación"""
        dialog = Gtk.MessageDialog(
            parent=self.gui_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="¿Estás seguro de reiniciar los contadores por aplicación?"
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.data_history["app_stats"] = {}
            self.save_data_history()
            GLib.idle_add(self.update_app_usage_page)
        dialog.destroy()
    
    def update_app_usage_page(self):
        """Actualizar la tabla de consumo por aplicación"""
        if not hasattr(self, "app_usage_list"):
            return

        self.app_usage_list.clear()
    
        # Obtener datos
        app_stats = self.data_history.get("app_stats", {})
        total_data = sum(data["total"] for data in app_stats.values())
    
        # Llenar la tabla
        for app_name, data in sorted(app_stats.items(), key=lambda x: x[1]["total"], reverse=True):
            percent = (data["total"] / total_data * 100) if total_data > 0 else 0
            self.app_usage_list.append([
                app_name,
                f"{data['download']:.2f}",  # Formato de 2 decimales
                f"{data['upload']:.2f}",
                f"{data['total']:.2f}",
                f"{percent:.1f}%"
            ])
    
    def clear_data_history(self, button):
        """Limpiar historial de consumo"""
        dialog = Gtk.MessageDialog(
            parent=self.gui_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="¿Eliminar historial de consumo?"
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            self.data_history["monthly_stats"] = {}
            self.save_data_history()
            self.update_data_history_page()
        dialog.destroy()
    
    def show_license_dialog(self, button):
        """Mostrar diálogo con la licencia completa (GPLv3)"""
        dialog = Gtk.Dialog(title="Licencia", parent=self.gui_window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
    
        # Configurar tamaño y estilo
        dialog.set_default_size(600, 400)
        content_area = dialog.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
    
        # Crear área de texto scrollable
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
    
        # TextView para mostrar la licencia
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
    
        # Insertar texto de licencia
        buffer = textview.get_buffer()
        gplv3_text = '''                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Use with the GNU Affero General Public License.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU Affero General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the special requirements of the GNU Affero General Public License,
section 13, concerning interaction through a network will apply to the
combination as such.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxGNU GENERAL PUBLIC LICENSE
    Version 3, 29 June 2007

    Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/> 
    Everyone is permitted to copy and distribute verbatim copies
    of this license document, but changing it is not allowed.

    Preamble

    The GNU General Public License is a free, copyleft license for
    software and other kinds of works.

    [...] (Aquí iría el texto completo de la GPL v3)y can decide which future
versions of the GNU General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If the program does terminal interaction, make it output a short
notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, your program's commands
might be different; for a GUI interface, you would use an "about box".

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU GPL, see
<https://www.gnu.org/licenses/>.

  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<https://www.gnu.org/licenses/why-not-lgpl.html>.
'''
    
        buffer.set_text(gplv3_text)
    
        # Añadir al scroll
        scrolled.add(textview)
        content_area.add(scrolled)
        dialog.show_all()
    
        # Ejecutar diálogo
        dialog.run()
        dialog.destroy()
    
    def check_for_updates(self, button):
        """Verificar si hay actualizaciones disponibles"""
        try:
            # Ejemplo usando git (ajustar según tu repositorio)
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
        
            local = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE)
            remote = subprocess.run(['git', 'rev-parse', 'origin/main'], stdout=subprocess.PIPE)
        
            if local.stdout.strip() != remote.stdout.strip():
                dialog = Gtk.MessageDialog(
                    parent=self.gui_window,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text="Hay actualizaciones disponibles"
                )
                dialog.format_secondary_markup(
                    "Se ha encontrado una nueva versión.\n"
                    "¿Deseas ir al repositorio para actualizar?"
                )
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    # Abrir repositorio en navegador
                    Gtk.show_uri_on_window(None, "https://github.com/alexx181207/lnetmon",  Gdk.CURRENT_TIME)
                dialog.destroy()
            else:
                dialog = Gtk.MessageDialog(
                    parent=self.gui_window,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="¡Estás actualizado!"
                )
                dialog.run()
                dialog.destroy()
            
        except Exception as e:
            dialog = Gtk.MessageDialog(
                parent=self.gui_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error al verificar actualizaciones"
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
    
    def on_gui_close(self, window):
        """Manejador para el cierre de la ventana GUI"""
        if self.gui_update_id:
            GLib.source_remove(self.gui_update_id)
            self.gui_update_id = None
        self.gui_window = None

    def exit_app(self, icon, item):
        """Manejar salida de la aplicación"""
        self.running = False
        
        # Cerrar ventana GUI si está abierta
        if self.gui_window:
            self.gui_window.destroy()
            
        # Detener el icono de bandeja
        if self.icon:
            self.icon.stop()
            
        
        # Liberar bloqueo de instancia única
        self.instance_lock.remove_lock()
            
        # Salir del programa
        sys.exit(0)

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