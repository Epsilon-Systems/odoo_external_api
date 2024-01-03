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
import traceback

print('----------------------------------------------------------------')
print('Bienvenido al proceso para creación de notas de crédito')
dir_path = os.path.dirname(os.path.realpath(__file__))
today_date = datetime.datetime.now()
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
print('----------------------------------------------------------------')

config_file_name = r'C:\Dev\wb_odoo_external_api\config_dev.json'

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
def autoinvoice():
    odoo_keys = get_odoo_access()
    psql_keys = get_psql_access()
    email_keys = get_email_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']
    # correo
    smtp_server = email_keys['smtp_server']
    smtp_port = email_keys['smtp_port']
    smtp_username = email_keys['smtp_username']
    smtp_password = email_keys['smtp_password']

    print('----------------------------------------------------------------')
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    print('Conectando a Mysql')
    # Connect to MySQL database
    mydb = mysql.connector.connect(
        host=psql_keys['dbhost'],
        user=psql_keys['dbuser'],
        password=psql_keys['dbpassword'],
        database=psql_keys['database']
    )
    mycursor = mydb.cursor()

    inv_id = 868162
    sale_id = 173425
    invoice_array = []

    sale_order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['id', '=', sale_id]]])[0]
    invoice_ids = sale_order['invoice_ids']
    print(f"Invoice ids antes de ejecutar: {invoice_ids}")
    for inv in invoice_ids:
        invoice_array.append(inv)
    invoice_array.append(inv_id)
    try:
        upd_sale = models.execute_kw(db_name, uid, password, 'sale.order', 'write', [[sale_id], {'invoice_ids': invoice_array}])
        sale_order_new = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['id', '=', sale_id]]])[0]
        invoice_ids_new = sale_order_new['invoice_ids']
        print(f"Invoice ids después de ejecutar: {invoice_ids_new}")
    except Exception as e:
        print(f"Error en: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    autoinvoice()