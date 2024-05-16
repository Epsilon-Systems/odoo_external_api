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
print('SCRIPT DE TAREAS PLANIFICADAS')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'C:\dev\odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def fetchmail_task():
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
    task_mail_in = 4
    task_mail_out = 2
    try:
        print(f"Tarea")
        print(f"Mail: Fetchmail Service")
        #task = models.execute_kw(db_name, uid, password, 'ir.cron', 'search_read', [[['id', '=', task_mail_in]]])[0]
        execute_task_in = models.execute_kw(db_name, uid, password, 'ir.cron', 'method_direct_trigger', [task_mail_in])
        print(f"Tarea")
        print(f"Mail: Gestor de colas de email")
        execute_task_out = models.execute_kw(db_name, uid, password, 'ir.cron', 'method_direct_trigger', [task_mail_out])
        print('----------------------------------------------------------------')
    except Exception as e:
       print(f"Error al ejecutar la tarea automática: {e}")

if __name__ == "__main__":
    fetchmail_task()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')