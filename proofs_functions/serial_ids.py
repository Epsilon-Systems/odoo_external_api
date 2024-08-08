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
# Archivo de configuración - Use config.json cuando los cambios vayan a producción
# Archivo de configuración - Use config_dev.json cuando los cambios vayan a pruebas
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
        # Leer el archivo de Excel con los IDs de las transferencias
        df = pd.read_excel(r'G:\Mi unidad\Dev\Operaciones\gasolina_operaciones.xlsx', sheet_name='Devoluciones')

        for index, row in df.iterrows():
            move_id = int(row['ID'])  # Convertir a tipo int
            print(f"Procesando devolución para la transferencia con ID: {move_id}")

            # Crear el wizard de devolución
            return_wizard_id = models.execute_kw(db_name, uid, password,'stock.return.picking', 'create', [{'picking_id': move_id}])
            search_ret = models.execute_kw(db_name, uid, password, 'stock.return.picking', 'search_read',[[['id', '=', return_wizard_id]]], {'limit': 1})
            if search_ret:
                return_wizard = search_ret[0]
                return_move_ids = return_wizard['product_return_moves']
                if not return_move_ids:
                        move_line = models.execute_kw(db_name, uid, password, 'stock.move.line', 'search_read', [[['picking_id', '=', move_id]]])#, {'fields': ['product_id', 'product_uom_qty'], 'limit': 1})
                        if move_line:
                            product_id = move_line[0]['product_id'][0]
                            quantity = move_line[0]['qty_done']
                            models.execute_kw(db_name, uid, password, 'stock.return.picking.line', 'create', [{
                                'product_id': product_id,
                                'quantity': quantity,
                                'wizard_id': return_wizard_id,
                                'move_id': move_id,
                                #'location_id':
                            }])
                # Confirmar la devolución
                result = models.execute_kw(db_name, uid, password,'stock.return.picking', 'create_returns', [return_wizard_id])
                print(f"Devolución creada exitosamente para el ID: {move_id}")
            else:
                print(f"No se creó la devolución de: {move_id}")

    except Exception as e:
        print(f"Error al crear la devolución: {e}")

if __name__ == "__main__":
    create_stock_moves()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')