import os
import sys
import numpy as np
from PIL import Image

#######################################
# CONFIGURACIÓN DE RUTAS
#######################################
INPUT_DIR = r"C:\Users\maste\OneDrive\Desktop\mi infancia\ipod"
OUTPUT_DIR = r"C:\Users\maste\OneDrive\Desktop\fotos recuperadas"

# Crear el directorio destino si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

#######################################
# FUNCIONES DE DECODIFICACIÓN DE YUV
#######################################
def normalize_value(val):
    """Convierte un valor de YUV para centrarlo en 0."""
    return val - 128

def yuv_to_rgb(y, u, v):
    """Convierte un píxel YUV a RGB."""
    r = y + 1.3983 * v
    g = y - 0.39465 * u - 0.5806 * v
    b = y + 2.03211 * u

    # Ajustar al rango [0, 255]
    r = int(min(max(0, r + 128), 255))
    g = int(min(max(0, g + 128), 255))
    b = int(min(max(0, b + 128), 255))
    return r, g, b

def get_rgb(chunk_data, offset, even):
    """Obtiene un píxel RGB desde datos YUV interlazados."""
    four_bytes = int.from_bytes(chunk_data[offset:offset+4], byteorder='big')
    y2 = four_bytes & 0xFF
    v =  (four_bytes >> 8) & 0xFF
    y1 = (four_bytes >> 16) & 0xFF
    u = (four_bytes >> 24) & 0xFF

    if even:
        return yuv_to_rgb(normalize_value(y1), normalize_value(u), normalize_value(v))
    else:
        return yuv_to_rgb(normalize_value(y2), normalize_value(u), normalize_value(v))

def process_chunk_yuv_interlaced_shared_chromiance(chunk_data, width, height):
    """
    Decodifica un bloque ithmb asumiendo:
    - Dimensiones: 720x480
    - YUV interlaced con crominancia compartida
    """
    rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
    num_pixels = width * height

    for y in range(height):
        y_over_2 = y // 2
        y_minus_1_over_2 = (y - 1) // 2
        for x in range(width):
            x_times_2 = x * 2
            x_minus_1_times_2 = (x - 1) * 2

            if y % 2 == 0: # fila par
                if x % 2 == 0:
                    offset = int(y_over_2 * width * 2 + x_times_2)
                    r,g,b = get_rgb(chunk_data, offset, True)
                else:
                    offset = int(y_over_2 * width * 2 + x_minus_1_times_2)
                    r,g,b = get_rgb(chunk_data, offset, False)
            else: # fila impar
                if x % 2 == 0:
                    offset = int(num_pixels + y_minus_1_over_2 * 2 * width + x_times_2)
                    r,g,b = get_rgb(chunk_data, offset, True)
                else:
                    offset = int(num_pixels + y_minus_1_over_2 * 2 * width + x_minus_1_times_2)
                    r,g,b = get_rgb(chunk_data, offset, False)

            rgb_data[y, x] = r, g, b

    return rgb_data

#######################################
# DECODIFICACIÓN DE ARCHIVOS ITHMB
#######################################
def decode_ithmb_to_image(input_file):
    """
    Decodifica un archivo ithmb asumiendo las dimensiones y formato de iPod Photo:
    720x480, YUV interlazado, crominancia compartida.
    """
    width, height = 720, 480
    processing_function = process_chunk_yuv_interlaced_shared_chromiance

    try:
        with open(input_file, 'rb') as f:
            total_bytes = width * height * 2
            chunk_data = f.read(total_bytes)
            if not chunk_data:
                print(f"Error: El archivo {input_file} está vacío o no es válido.")
                return None

            rgb = processing_function(chunk_data, width, height)
            img = Image.fromarray(rgb)
            return img
    except IOError as e:
        print(f"Error al leer {input_file}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado decodificando {input_file}: {e}")
        return None

#######################################
# GUARDADO DE IMÁGENES
#######################################
def save_as_jpg(img, output_path):
    """Guarda la imagen como JPEG."""
    # Convertir a RGB si tiene transparencia
    if img.mode in ('RGBA', 'LA'):
        img = img.convert('RGB')
    img.save(output_path, 'JPEG', quality=90)

def process_ithmb_file(input_path, output_dir):
    """Procesa un archivo ithmb (decodifica y guarda como .jpg)."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, base_name + '.jpg')
    img = decode_ithmb_to_image(input_path)
    if img is not None:
        save_as_jpg(img, output_path)
        print(f"Convertido: {input_path} -> {output_path}")
    else:
        print(f"No se pudo decodificar {input_path}")

#######################################
# FUNCIÓN PRINCIPAL
#######################################
def main():
    # Verificar que el directorio de entrada exista
    if not os.path.isdir(INPUT_DIR):
        print(f"La carpeta de origen no existe: {INPUT_DIR}")
        return

    # Listar archivos .ithmb
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.ithmb')]
    if not files:
        print("No se encontraron archivos .ithmb en la carpeta de origen.")
        return

    for ithmb_file in files:
        ithmb_path = os.path.join(INPUT_DIR, ithmb_file)
        if os.path.isfile(ithmb_path):
            process_ithmb_file(ithmb_path, OUTPUT_DIR)

    print("¡Proceso concluido!")

if __name__ == "__main__":
    main()
