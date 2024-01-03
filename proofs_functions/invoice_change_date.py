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

server_url  ='https://wonderbrands-v3-8866939.dev.odoo.com'
db_name = 'wonderbrands-v3-8866939'
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
inv_ids = [601860,601861,601862,601863,601864,601865,601866,601867,601868,601869,601870,601871,601872,601873,601874,601875,601876,601877,601878,601879,601880,601881,601882,601883,601884,601885,601886,601887,601888,601889,601890,601891,601892,601893,601894,601895,601896,601898,601899,601900,601901,601902,601903,601904,601905,601906,601907,601908,601909,601910,601911,601912,601913,601914,601915,601916,601917,601918,601919,601920,601921,601922,601923,601924,601925,601926,601927,601928,601929,601930,601931,601932,601933,601934,601935,601936,601937,601938,601939,601940,601941,601942,601943,601944,601945,601946,601947,601948,601949,601950,601951,601952,601953,601954,601955,601956,601957,601958,601959,601960,601961,601962,601963,601964,601965,601966,601967,601968,601969,601970,601971,601972,601973,601974,601975,601976,601977,601978,601979,601980,601981,601982,601983,601984,601985,601986,601987,601988,601989,601990,601991,601992,601993,601994,601995,601996,601997,601998,601999,602000,602001,602002,602003,602004,602005,602006,602007,602008,602009,602010,602011,602012,602013,602014,602015,602016,602017,602018,602019,602020,602021,602022,602023,602024,602025,602026,602027,602028,602029,602030,602031,602032,602033,602034,602035,602036,602037,602038,602039,602040,602041,602042,602043,602044,602045,602046,602047,602048,602049,602050,602051,602052,602053,602054,602055,602056,602057,602058,602059,602060,602061,602062,602063,602064,602065,602066,602067,602068,602069,602070,602071,602072,602073,602074,602075,602076,602077,602078,602079,602080,602081,602082,602083,602084,602085,602086,602087,602088,602089,602090,602091,602092,602093,602094,602095,602096,602097,602098,602099,602100,602101,602102,602103,602104,602105,602106,602107,602108,602109,602110,602111,602112,602113,602114,602115,602116,602117,602118,602119,602120,602121,602122,602123,602124,602125,602126,602127,602128,602129,602130,602131,602132,602133,602134,602135,602136,602137,602138,602139,602140,602141,602142,602143,602144,602145,602146,602147,602148,602149,602150,602151,602152,602153,602154,602155,602156,602157,602158,602159,602160,602161,602162]
inv_names = []
#Ciclo que ordena las SO, los UUIDS y las fechas en un diccionario
for row in inv_ids:
    print(f"ID de factura a editar: {row}")
    search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', row]]])

    inv_name = search_inv[0]['name']
    inv_date = search_inv[0]['invoice_date']
    print(f"Factura publicada: {inv_name}")
    upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[row], {'invoice_payment_term_id': 1}])
    inv_names.append(inv_name)
    print('----------------------------------------------------------------')

print(f"Nombre de las facturas modificadas: {inv_names}")
