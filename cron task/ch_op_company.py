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
#import MySQLdb
#import mysql.connector
#import smtplib
#import ssl
#import email
import datetime

print('================================================================')
print('SCRIPT DE TAREAS PLANIFICADAS')
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
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')
    print('----------------------------------------------------------------')
    excel_file_inv = r'C:\dev\odoo_external_api\cron task\files\correction_file.xlsx'
    file_inv = pd.read_excel(excel_file_inv, usecols=['ID'])
    invoice_records = file['ID'].tolist()
    invoice_names = []
    inv_not_found = []
    inv_ids = []
    so_names = []
    so_ids = []
    so_not_found = []

    progress_bar = tqdm(total=len(invoice_records), desc="Procesando")

    try:
        for each in invoice_records:
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', each]]])[0]
            if invoice:
                inv_origin = invoice.name
                inv_id = invoice.id
                inv_state = invoice.state
                inv_company = invoice.company_id.id
                sale = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['name', '=', inv_originv]]])[0]
                if sale:
                    sale_name = sale.name
                    sale_id = sale.id
                    sale_state = sale.state
                    sale_company = invoice.company_id.id
                    upd_inv_company = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[inv_id], {'company_id': 7}])
                    upd_so_company = models.execute_kw(db_name, uid, password, 'sale.order', 'write',[[sale_id], {'company_id': 7}])
                    if inv_state == 'draft':
                        upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post',[inv_id])
                        chk_invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', inv_id]]])[0]
                        chk_company_id = chk_invoice.company_id.id
                        chk_inv_name = chk_invoice.name
                        if chk_company_id == 7:
                            invoice_names.append(chk_inv_name)
                        else:
                            double_chk_inv = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[inv_id], {'company_id': 7}])
                            invoice_names.append(chk_inv_name)
                    else:
                        pass
                else:
                    pass
            else:
                pass

    except Exception as e:
       print(f"Error al ejecutar la tarea automática: {e}")

if __name__ == "__main__":
    fetchmail_task()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')