import json
import jsonrpc
import jsonrpclib
import getpass
import http
import requests
import os
import xmlrpc.client
import time
import datetime

print('================================================================')
print('RFID Module access')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
#Archivo de configuración - Use config_dev.json cuando los cambios vayan a pruebas
config_file_name = r'C:\dev\odoo_external_api\config\config_dev.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def rfid_api_connection():
    try:
        url = "http://websdk.polimex.online/sdk/details.json"  # Ejemplo de URL, ajustar según SDK
        headers = {
            "Authorization": "Bearer tu_token",  # Autenticación
            "Content-Type": "application/json",
        }
        data = {
            "codigo_rfid": '0008756935'
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()  # Validación exitosa
        else:
            return {"error": response.text}

    except Exception as e:
        print(f"Error al ejecutar la tarea automática: {e}")
if __name__ == "__main__":
    rfid_api_connection()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')