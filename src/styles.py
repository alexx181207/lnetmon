#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFilter
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango




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
