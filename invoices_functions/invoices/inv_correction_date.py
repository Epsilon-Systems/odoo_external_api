from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from pprint import pprint
from email import encoders
from tqdm import tqdm
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
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime

print('================================================================')
print('BIENVENIDO AL PROCESO DE CORRECCIÓN DE FECHA DE FACTURA')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha: ' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
folder = r'C:\Dev\wb_odoo_external_api'
config_file_name = r'C:\Dev\wb_odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['odoo']
def get_psql_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['psql']
def get_email_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['email']
def correction_date():
    odoo_keys = get_odoo_access()
    psql_keys = get_psql_access()
    email_keys = get_email_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']

    print('----------------------------------------------------------------')
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')
    print('----------------------------------------------------------------')
    excel_file_path = r'C:\Dev\wb_odoo_external_api\invoices_functions\files\corrections\correction_date.xlsx'
    file = pd.read_excel(excel_file_path, usecols=['ID'])
    invoice_records = file['ID'].tolist()

    invoice_id = []
    invoice_team = []
    invoice_previous_date = []
    invoice_edi_state = []
    invoice_new_date = []
    invoice_diff_status = []

    progress_bar = tqdm(total=len(invoice_records), desc="Procesando")

    for each in invoice_records:
        try:
            int_id = int(each)
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', int_id]]])[0]

            if invoice:
                inv_state = invoice['state']
                if inv_state == 'draft':
                    inv_id = invoice['id'] #Id de la factura
                    inv_team = invoice['team_id'][1] #Equipo de ventas
                    inv_date = invoice['invoice_date'] #Fecha de factura
                    inv_term_id = invoice['invoice_payment_term_id'] #Terminos de la fecha de pago
                    inv_edi_state = invoice['edi_state'] #Estado de la facturación
                    new_date = today_date.strftime("%Y-%m-%d") #Nueva fecha (fecha del día de hoy)
                    #Actualiza la fecha de la factura
                    upd_invoice_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[inv_id], {'invoice_date': new_date}])
                    upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[inv_id], {'invoice_payment_term_id': 1}])
                    #Agrega registros a las listas para uso del excel
                    invoice_id.append(inv_id)
                    invoice_team.append(inv_team)
                    invoice_previous_date.append(inv_date)
                    invoice_edi_state.append(inv_edi_state)
                    invoice_new_date.append(new_date)
                    progress_bar.update(1)
                else:
                    print(f"El estatus de esta factura {int_id} no es Borrador")
                    invoice_diff_status.append(int_id)
            else:
                print(f"El ID de la factura {int_id} no existe en Odoo")
                progress_bar.update(1)
        except Exception as e:
            print(f"Error al cambiar la fecha de la factura {int_id}: {e}")
    # Crear excel
    try:
        print('Creando archivo Excel')
        print('----------------------------------------------------------------')

        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'invoice_id'
        sheet['B1'] = 'invoice_team'
        sheet['C1'] = 'invoice_previous_date'
        sheet['D1'] = 'invoice_edi_state'
        sheet['E1'] = 'invoice_new_date'
        sheet['F1'] = 'invoice_diff_status'

        # Agregar los resultados de los arrays
        for i in range(len(invoice_id)):
            sheet['A{}'.format(i + 2)] = invoice_id[i]
        for i in range(len(invoice_team)):
            sheet['B{}'.format(i + 2)] = invoice_team[i]
        for i in range(len(invoice_previous_date)):
            sheet['C{}'.format(i + 2)] = invoice_previous_date[i]
        for i in range(len(invoice_edi_state)):
            sheet['D{}'.format(i + 2)] = invoice_edi_state[i]
        for i in range(len(invoice_new_date)):
            sheet['E{}'.format(i + 2)] = invoice_new_date[i]
        for i in range(len(invoice_diff_status)):
            sheet['E{}'.format(i + 2)] = invoice_diff_status[i]

        # Guardar el archivo Excel en disco
        excel_file = 'facturas_fecha_modificada' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)
        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as e:
        print(f"Error al crear el archivo de excel: {e}")

    progress_bar.close()

if __name__ == "__main__":
    correction_date()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')