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
config_file_name = r'C:\dev\odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def stamp_invoices():
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
    # Lista que contedrá los ids de las transferencias creadas
    inv_id = 260007
    try:
        invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', inv_id]]])[0]
        inv_name = invoice['name']
        inv_id_real = invoice['id']
        print(f"Se encontró la factura {inv_name} con ID: {inv_id_real}")
        print('----------------------------------------------------------------')
        print('Publicando')
        print('----------------------------------------------------------------')
        upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [inv_id_real])
        print(f'La factura {inv_name} se ha actualizado correctamente')
        print('----------------------------------------------------------------')
        print('Verificando')
        invoice_ver = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', inv_id_real]]])[0]
        inv_name_ver = invoice['name']
        inv_id_real_ver = invoice['id']
        uuid_ver = invoice['l10n_mx_edi_cfdi_uuid']
        print(inv_name_ver)
        print(inv_id_real_ver)
        print(uuid_ver)

    except Exception as e:
        print(f"Error al actualizar la factura: {e}")

if __name__ == "__main__":
    stamp_invoices()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duración del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')