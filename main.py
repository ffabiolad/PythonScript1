import os
import hashlib
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

# rutas principales, 1.- de donde se toman las fotos y 2.- donde se organizan
SOURCE_DIR = "/Volumes/Memoria/Fotos Sin Orden"
DEST_DIR = "/Volumes/Memoria/Fotos Organizadas"

# extensiones que vamos a considerar como fotos y videos
PHOTO_EXT = [".jpg", ".jpeg", ".png"]
VIDEO_EXT = [".mp4", ".mov", ".avi", ".mkv"]

def get_file_hash(path, block_size=65536):
    """ hash único para detectar duplicados"""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        buf = f.read(block_size)
        while buf:
            hasher.update(buf)
            buf = f.read(block_size)
    return hasher.hexdigest()

def get_exif_date(path):
    """leer la fecha de captura de una foto desde los metadatos EXIF"""
    try:
        image = Image.open(path)
        info = image._getexif()
        if info:
            for tag, value in info.items():
                if TAGS.get(tag) == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None

def get_file_date(path):
    """Devuelve la mejor fecha disponible (EXIF o fecha de creación del archivo)"""
    if any(path.lower().endswith(ext) for ext in PHOTO_EXT):
        date = get_exif_date(path)
        if date:
            return date
    # si no hay EXIF, usar la fecha del sistema
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts)

def organize_files():
    seen_hashes = {}
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            #  archivos ocultos o temporales (._ o .DS_Store)
            if file.startswith("._") or file.startswith("."):
                continue

            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()

            if ext not in PHOTO_EXT + VIDEO_EXT:
                continue  # ignorar archivos que no son foto o video

            # detectar duplicados
            try:
                filehash = get_file_hash(filepath)
            except FileNotFoundError:
                print(f" Saltando archivo corrupto o invisible: {filepath}")
                continue

            if filehash in seen_hashes:
                print(f"Duplicado encontrado: {filepath} (igual que {seen_hashes[filehash]})")
                continue
            else:
                seen_hashes[filehash] = filepath

            # obtener fecha
            date = get_file_date(filepath)
            year = date.strftime("%Y")

            # crear carpeta destino
            year_folder = os.path.join(DEST_DIR, year)
            os.makedirs(year_folder, exist_ok=True)

            # mover archivo
            new_path = os.path.join(year_folder, file)

            # evita sobreescribir si ya existe un archivo con el mismo nombre
            if os.path.exists(new_path):
                base, ext = os.path.splitext(file)
                i = 1
                while os.path.exists(new_path):
                    new_filename = f"{base}_{i}{ext}"
                    new_path = os.path.join(year_folder, new_filename)
                    i += 1

            shutil.move(filepath, new_path)
            print(f"Movido: {filepath} → {new_path}")

if __name__ == "__main__":
    organize_files()
