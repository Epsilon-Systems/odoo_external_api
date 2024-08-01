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
print('SCRIPT DE DESCARGA DE ASISTENCIA EMPLEADOS')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
#Archivo de configuración - Use config_dev.json cuando los cambios vayan a pruebas
config_file_name = r'C:\dev\odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def attendance_task_zk():
    # Obtener credenciales
    odoo_keys = get_odoo_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    id_zk = 1
    try:
        print(f"Tarea:")
        print(f"Intentando conexión con ZK machine")
        try_connection = models.execute_kw(db_name, uid, password, 'zk.machine', 'try_connection', [id_zk])
        print(f"Tarea:")
        print(f"Descarga de registros de asistencia")
        attendance = models.execute_kw(db_name, uid, password, 'zk.machine', 'download_attendance', [id_zk])
        print('----------------------------------------------------------------')
    except Exception as e:
       print(f"Error al ejecutar la tarea automática: {e}")

if __name__ == "__main__":
    attendance_task_zk()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')