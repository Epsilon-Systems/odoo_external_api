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
#server_url  ='https://wonderbrands-v3-8443304.dev.odoo.com'
#db_name = 'wonderbrands-v3-8443304'
#username = 'admin'
#password = 'admin123'

server_url  ='https://wonderbrands-v3-8915998.dev.odoo.com'
db_name = 'wonderbrands-v3-8915998'
username = 'admin'
password = 'nK738*rxc#nd'

print('----------------------------------------------------------------')
print('SCRIPT DE CREACIÓN DE FACTURAS POR SO')
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
inv_ids = [611313]
inv_names = []
inv_real_date = '2023-06-28 15:22:12'
inv_line_ids = []
try:
    for row in inv_ids:
        print(f"ID de factura a editar: {row}")
        upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[row], {'invoice_date': inv_real_date}])
        upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[row], {'invoice_payment_term_id': 1}])
        #Busca la factura y obtiene el nombre y la fecha ya actualizada
        search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', row]]])
        inv_name = search_inv[0]['name']
        inv_date = search_inv[0]['invoice_date']
        print(f"Factura: {inv_name} Fecha: {inv_date}")

        account_line_ids = models.execute_kw(db_name, uid, password, 'account.move.line', 'search_read',[[['move_id', '=', inv_name]]])
        for each in account_line_ids:
            move_id = each['id']
            name_move_id = each['account_id'][1]
            if name_move_id == '107.05.01 Mercancías Enviadas - No Facturas' or name_move_id == '501-001-001 COSTO DE VENTA':
                #change_journal_date = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date': inv_date}])
                change_journal_mat = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date_maturity': inv_date}])
            else:
                change_journal_date = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date': inv_date}])
                change_journal_mat = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date_maturity': inv_date}])
            print(f"Nombre del Apunte de diario: {name_move_id}")
        inv_names.append(inv_name)
        print('----------------------------------------------------------------')
except Exception as e:
    print(f"Error al crear la factura de la orden: {e}")

print(f"Nombre de las facturas modificadas: {inv_names}")
print('Proceso terminado')