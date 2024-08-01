from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from pprint import pprint
from email import encoders
from tqdm import tqdm
from datetime import datetime
import time
import json
import jsonrpc
import jsonrpclib
import random
import urllib.request
import getpass
import http
import requests
import logging
import zipfile
import socket
import os
import locale
import xmlrpc.client
import base64
import openpyxl
import xlrd
import pandas as pd
import smtplib
import ssl
import email
import datetime

print('================================================================')
print('SCRIPT DE TAREAS PLANIFICADAS')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
# Establecer la configuración regional a español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
#Archivo de configuración - Use config_dev.json cuando los cambios vayan a pruebas
config_file_name = r'C:\dev\odoo_external_api\config\config_dev.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def create_stock_moves():
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
    try:
        #progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
        excel_file_path = r'G:\Mi unidad\Dev\Operaciones\gasolina_operaciones.xlsx'
        df = pd.read_excel(r'G:\Mi unidad\Dev\Operaciones\gasolina_operaciones.xlsx', sheet_name='Data')
        for index, row in df.iterrows():
            move_line_id = int(row['move_line'])
            move_id = 353
            picking_id = models.execute_kw(db_name, uid, password, 'stock.move.line', 'search_read',[[['picking_id', '=', move_line_id]]])#, {'limit': 1})
            picking_move_line_id = picking_id[0]['id']
            #picking_move_line_name = picking_id[0]['name']
            upd_move_line = models.execute_kw(db_name, uid, password, 'stock.move.line', 'write',[[picking_move_line_id], {'lot_ids': move_id}])
            print(upd_move_line)

    except Exception as e:
       print(f"Error al crear el movimiento de almacén: {e}")

if __name__ == "__main__":
    create_stock_moves()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')