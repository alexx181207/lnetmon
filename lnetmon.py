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
        web_label.set_markup('<a href="https://github.com/tuusuario/internet-monitor">GitHub</a>') 
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
        """if hasattr(self, "data_history_window"):
            self.update_data_history_page()"""
              
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
        gplv3_text = '''GNU GENERAL PUBLIC LICENSE
    Version 3, 29 June 2007

    Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/> 
    Everyone is permitted to copy and distribute verbatim copies
    of this license document, but changing it is not allowed.

    Preamble

    The GNU General Public License is a free, copyleft license for
    software and other kinds of works.

    [...] (Aquí iría el texto completo de la GPL v3)'''
    
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
                    Gtk.show_uri_on_window(None, "https://github.com/tuusuario/internet-monitor",  Gdk.CURRENT_TIME)
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