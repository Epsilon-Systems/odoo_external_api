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
import shutil

print('----------------------------------------------------------------')
print('Bienvenido al proceso para creación de notas de crédito')
dir_path = os.path.dirname(os.path.realpath(__file__))
today_date = datetime.datetime.now()
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
print('----------------------------------------------------------------')

config_file_name = r'C:/Dev/wb_odoo_external_api/config_dev.json'

def extract():
    # Ruta de la carpeta de origen
    carpeta_origen = 'G:/Mi unidad/xml_sr_mkp_invoices/Octubre/'

    # Ruta de la carpeta de destino
    carpeta_destino = 'G:/Mi unidad/xml_sr_mkp_invoices/Octubre/'

    # Recorre todas las subcarpetas de la carpeta de origen
    for root, dirs, files in os.walk(carpeta_origen):
        # Itera sobre todos los archivos en la subcarpeta actual
        for archivo in files:
            # Ruta completa del archivo actual
            ruta_archivo = os.path.join(root, archivo)
            # Ruta de destino en carpeta_origen
            ruta_destino = os.path.join(carpeta_origen, archivo)

            # Copia el archivo a la carpeta de origen, reemplazando si es necesario
            shutil.copy2(ruta_archivo, ruta_destino)

    print("Archivos extraídos exitosamente en", carpeta_origen)

if __name__ == "__main__":
    extract()