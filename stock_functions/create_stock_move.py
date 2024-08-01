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
        #Define la ubicación y el nombre del archivo de excel
        df = pd.read_excel(r'G:\Mi unidad\Dev\Operaciones\gasolina_operaciones.xlsx', sheet_name='Data')
        for index, row in df.iterrows():
            int_date = row['date'].strftime('%Y-%m-%d')
            location_id = row['location_id']
            location_dest_id = row['location_dest_id']
            no_ticket = row['no_ticket']
            no_serie = row['no_serie']
            product_id = 40
            product_qty = 1
            #Busca el registro exacto entre el excel y la ubicación de origen en Odoo
            location_id_from = models.execute_kw(db_name, uid, password, 'stock.location', 'search_read',[[['complete_name', '=', location_id]]], {'limit': 1})
            if location_id_from:
                loc_id_from = location_id_from[0]['id']
            else:
                print(f'No se encontró la ubicación de origen: {location_id}')
                continue
            #Busca el registro más parecido entre el excel y la ubicación de destino en Odoo
            location_id_to = models.execute_kw(db_name, uid, password, 'stock.location', 'search_read',[[['name', 'ilike', location_dest_id]]], {'limit': 1})
            if location_id_to:
                location_id_to = location_id_to[0]['id']
            else:
                print(f'No se encontró la ubicación de destino: {location_dest_id}')
                continue
            #Busca el número de serie de la tarjeta de gasolina
            serie_id = models.execute_kw(db_name, uid, password, 'stock.lot', 'search_read',[[['name', '=', no_serie]]])  # , {'limit': 1})
            lot_id = int(serie_id[0]['id'])
            #Define los datos de la transferencia interna
            print('Definiendo datos de transferencia interna')
            picking_data = {
                'scheduled_date': int_date,#today_date.strftime("%Y-%m-%d"),
                'partner_id': 1,  # ID del socio al que se envía la transferencia
                'location_id': loc_id_from,  # ID de la ubicación de origen
                'location_dest_id': location_id_to,  # ID de la ubicación de destino
                'picking_type_id': 5,  # ID del tipo de operación (por ejemplo, envío)
                'x_studio_no_ticket': no_ticket,
                'x_studio_creado_por_api': True,
                'move_ids_without_package': [
                    (0, 0, {
                        'name': 'Tarjetas Empresariales',  # Nombre del producto
                        'product_id': 49,  # ID del producto
                        'product_uom_qty': 1,  # Cantidad a transferir
                        'product_uom': 1,  # Unidad de medida
                        'location_id': loc_id_from,  # ID de la ubicación de origen del movimiento
                        'location_dest_id': location_id_to,  # ID de la ubicación de destino del movimiento
                        'lot_ids': [(4, lot_id)]
                    }),
                ],
            }
            # Contexto con la zona horaria
            context = {'tz': 'America/Mexico_City'}
            # Crear la transferencia
            picking_id = models.execute_kw(db_name, uid, password, 'stock.picking', 'create', [picking_data],{'context': context})
            #Marcar por realizar la transferencia
            picking_upd = models.execute_kw(db_name, uid, password, 'stock.picking', 'action_confirm', [picking_id])

    except Exception as e:
       print(f"Error al crear el movimiento de almacén: {e}")

if __name__ == "__main__":
    create_stock_moves()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')