import time

from flask import Flask, render_template, request, make_response, url_for, session
import json
import jsonrpc
import jsonrpclib
import random
import urllib.request
import getpass
import http
import requests
from pprint import pprint
import logging
import zipfile
import socket
import os
import xmlrpc.client
import base64
import openpyxl
import xlrd
import pandas as pd
#import MySQLdb
import mysql.connector

#API Configuration
dir_path = os.path.dirname(os.path.realpath(__file__))
server_url  ='https://wonderbrands.odoo.com'
db_name = 'wonderbrands-main-4539884'
username = 'admin'
password = '9Lh5Z0x*bCqV'

#server_url  ='https://wonderbrands-vobitest-9144251.dev.odoo.com'
#db_name = 'wonderbrands-vobitest-9144251'
#username = 'admin'
#password = '9Lh5Z0x*bCqV'

print('----------------------------------------------------------------')
print('SCRIPT DE VALIDACIÓN DE FACTURAS')
print('----------------------------------------------------------------')
print('Conectando API Odoo')
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
uid = common.authenticate(db_name, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
print(common)
print('Conexión con Odoo establecida')
print('----------------------------------------------------------------')
print('Obteniendo información')
print('----------------------------------------------------------------')
inv_ids = [729381,729409,729425]
inv_names = []
#Ciclo que ordena las SO, los UUIDS y las fechas en un diccionario
for row in inv_ids:
    print(f"ID de factura a editar: {row}")
    upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post',[row])
    search_inv_name = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', row]]])
    inv_name = search_inv_name[0]['name']
    print(f"Factura publicada: {inv_name}")
    inv_names.append(inv_name)
    print('----------------------------------------------------------------')

print(f"Nombre de las facturas creadas: {inv_names}")
print(f"IDs de las facturas creadas: {inv_ids}")
