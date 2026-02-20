from pprint import pprint
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
import datetime

print('================================================================')
print('CAMBIAR RESPONSABLE')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'E:\Dev\odoo_external_api\config\config.json'

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

def change_responsible_id():
    # Obtener credenciales
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
    print('Leyendo archivo')
    excel_file_path = r'E:\Dev\odoo_external_api\stock_functions\files\responsible_id.xlsx'
    sale_file = pd.read_excel(excel_file_path, usecols=['ID'])
    product_ids = sale_file['ID'].tolist()
    progress_bar = tqdm(total=len(product_ids), desc="Procesando")
    try:
        print('Vaya por otro tecito u otro café porque este proceso tomará unos minutos')
        print('----------------------------------------------------------------')
        # Consultamos a sale.order para obtener los campos requeridos de cada orden de venta
        for each in product_ids:
            products = models.execute_kw(db_name, uid, password, 'product.product', 'search_read', [[['id', '=', each]]])[0]
            if products:
                product_id = products['id']
                product_tmpl = products['product_tmpl_id'][0]
                if product_id:
                    product_tmpl_id = models.execute_kw(db_name, uid, password, 'product.template', 'search_read', [[['id', '=', product_tmpl]]])[0]
                    responsible = product_tmpl_id['responsible_id'][0]
                    responsible_name = product_tmpl_id['responsible_id'][1]
                    upd_responsible = models.execute_kw(db_name, uid, password, 'product.template', 'write', [[product_tmpl], {'responsible_id': 1936}])
                    check_responsible = products = models.execute_kw(db_name, uid, password, 'product.template', 'search_read', [[['id', '=', product_tmpl]]])[0]
                    check_name = check_responsible['responsible_id'][1]

                    message = {
                        'body': f'El responsable de este producto fue cambiado vía API por el área de IT de: {responsible_name} a {check_name}',
                        'message_type': 'comment',
                    }
                    write_msg_tech = models.execute_kw(db_name, uid, password, 'product.template', 'message_post', [product_tmpl], message)
                else:
                    print(f"No existe plantilla de producto que corresponda a {product_id}")
                    continue
            else:
                print(f"No existe un producto que corresponda a {each}")
                continue

    except Exception as e:
        print(f"Error al crear la factura con error: {e}")

    progress_bar.close()

if __name__ == "__main__":
    change_responsible_id()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duraciòn del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')