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
print('SCRIPT DE VALIDACIÓN DE MOVIMIENTOS DE ALMACÉN')
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
stock_ids = [789259]
stock_names = []
#Ciclo que ordena las SO, los UUIDS y las fechas en un diccionario
for row in stock_ids:
    upd_stock_state = models.execute_kw(db_name, uid, password, 'stock.picking', 'button_validate',[row])
    search_stock_name = models.execute_kw(db_name, uid, password, 'stock.picking', 'search_read',[[['id', '=', row]]])
    stock_name = search_stock_name[0]['name']
    print(f"Movimiento validado: {stock_name}")
    stock_names.append(stock_name)
    print('----------------------------------------------------------------')

print(f"Nombre de los movimientos validados: {stock_names}")
print(f"IDs de las transferencias: {stock_ids}")
