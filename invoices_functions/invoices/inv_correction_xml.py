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
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime

print('================================================================')
print('BIENVENIDO AL PROCESO DE CORRECCIÓN DE FACTURAS')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
# Establecer la configuración regional a español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'C:\Dev\wb_odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['odoo']
def correction_stamp():
    odoo_keys = get_odoo_access()
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
    excel_file_path = r'C:\Dev\wb_odoo_external_api\invoices_functions\files\corrections\correction_file.xlsx'
    file = pd.read_excel(excel_file_path, usecols=['ID'])
    invoice_records = file['ID'].tolist()

    invoice_names = []
    inv_partners = []
    previous_edi_use = []
    new_edi_use = []
    inv_ids = []
    so_names = []
    xml_name = []
    inv_dats = []
    no_xml_adj = []

    progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
    try:
        for each in invoice_records:
            int_id = int(each)
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', int_id]]])[0]
            attachment = models.execute_kw(db_name, uid, password, 'ir.attachment', 'search_read', [[['res_id', '=', int_id]]])[0]
            edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'search_read',[[['move_id', '=', int_id]]])
            if invoice:
                inv_date = invoice['invoice_date'] #Fecha de la factura actual
                date_obj = datetime.datetime.strptime(inv_date, '%Y-%m-%d') #Establece el campo como datetime
                name_month = date_obj.strftime('%B') #Convierte el número del mes a texto
                inv_name = invoice['name'] #Nombre de la factura
                inv_so = invoice['invoice_origin'] #Origen de la factura
                inv_partner = invoice['partner_id'][1] #Nombre del partner
                inv_edi_usage = invoice['l10n_mx_edi_usage'] #Uso del CFDI
                edi_inv_state = invoice['edi_state'] #Estado de facturación
                edi_uuid = invoice['l10n_mx_edi_cfdi_uuid'] #Folio fiscal
                if edi_inv_state != 'sent':
                    if attachment:
                        att_name = attachment['name'] #Nombre del archivo adjunto
                        att_id = attachment['id'] #ID del archivo adjunto
                        if edi_document:
                            for edi in edi_document:
                                edi_id = edi['id'] #ID del registro en la tabla EDI
                                edi_name = edi['edi_format_name'] #Nombre del registro en la tabla EDI
                                edi_state = edi['state'] # Estado del registro en la tabla EDI
                                if edi_name == 'CFDI (3.3)':
                                    if inv_partner == 'PÚBLICO EN GENERAL':
                                        #Actualiza el uso del CFDI a Sin efectos fiscales si el partner es PÚBLICO EN GENERAL
                                        upd_edi_usage = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[int_id], {'l10n_mx_edi_usage': 'S01'}])
                                        #Elimina el registro de la tabla EDI.DOCUMENT
                                        del_edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','unlink', [[edi_id]])
                                        #Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                        values = [{
                                            'move_id': int_id,
                                            'edi_format_id': 2,
                                            'attachment_id': att_id,
                                            'state': 'sent',
                                            'create_uid': 1,
                                            'write_uid': 2,
                                        }]
                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                        new_edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'create',values)
                                        invoice_names.append(inv_name)
                                        inv_partners.append(inv_partner)
                                        previous_edi_use.append(inv_edi_usage)
                                        inv_ids.append(int_id)
                                        so_names.append(inv_so)
                                        xml_name.append(att_name)
                                        inv_dats.append(inv_date)
                                        progress_bar.update(1)
                                    else:
                                        # Elimina el registro de la tabla EDI.DOCUMENT
                                        del_edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','unlink', [[edi_id]])
                                        # Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                        values = [{
                                            'move_id': int_id,
                                            'edi_format_id': 2,
                                            'attachment_id': att_id,
                                            'state': 'sent',
                                            'create_uid': 1,
                                            'write_uid': 2,
                                        }]
                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                        new_edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','create', values)
                                        invoice_names.append(inv_name)
                                        inv_partners.append(inv_partner)
                                        previous_edi_use.append(inv_edi_usage)
                                        inv_ids.append(int_id)
                                        so_names.append(inv_so)
                                        xml_name.append(att_name)
                                        inv_dats.append(inv_date)
                                        progress_bar.update(1)
                                else:
                                    continue
                        else:
                            print(f"La factura {int_id} no tiene un registro EDI")
                            progress_bar.update(1)
                            continue
                    else:
                        print(f"La factura {int_id} no tiene XML adjunto")
                        no_xml_adj.append(inv_name)
                        progress_bar.update(1)
                        continue
                else:
                    print(f"La factura {inv_name} ya fue modificada")
                    progress_bar.update(1)
                    continue
            else:
                print(f"No existe la factura {int_id}")
                continue
    except Exception as i:
        print(f"Error: no se pudieron corregir las facturas: {i}")
    try:
        print("Creando excel")
        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'invoice_names'
        sheet['B1'] = 'inv_partners'
        sheet['C1'] = 'previous_edi_use'
        sheet['D1'] = 'new_edi_use'
        sheet['E1'] = 'inv_ids'
        sheet['F1'] = 'so_names'
        sheet['G1'] = 'xml_name'
        sheet['H1'] = 'inv_dats'
        sheet['I1'] = 'no_xml_adj'

        # Agregar los resultados de los arrays
        for i in range(len(invoice_names)):
            sheet['A{}'.format(i + 2)] = invoice_names[i]
        for i in range(len(inv_partners)):
            sheet['B{}'.format(i + 2)] = inv_partners[i]
        for i in range(len(previous_edi_use)):
            sheet['C{}'.format(i + 2)] = previous_edi_use[i]
        for i in range(len(new_edi_use)):
            sheet['D{}'.format(i + 2)] = new_edi_use[i]
        for i in range(len(inv_ids)):
            sheet['E{}'.format(i + 2)] = inv_ids[i]
        for i in range(len(so_names)):
            sheet['F{}'.format(i + 2)] = so_names[i]
        for i in range(len(xml_name)):
            sheet['G{}'.format(i + 2)] = xml_name[i]
        for i in range(len(inv_dats)):
            sheet['H{}'.format(i + 2)] = inv_dats[i]
        for i in range(len(no_xml_adj)):
            sheet['I{}'.format(i + 2)] = no_xml_adj[i]

        # Guardar el archivo Excel en disco
        excel_file = 'correction_invoices_WM_' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)
        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as e:
        print(f"Error al crear el archivo de excel: {e}")

    progress_bar.close()

if __name__ == "__main__":
    correction_stamp()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')