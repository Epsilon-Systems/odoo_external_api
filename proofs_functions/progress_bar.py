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

#API Configuration
dir_path = os.path.dirname(os.path.realpath(__file__))
print('----------------------------------------------------------------')
print('Bienvenido al proceso de facturación')
today_date = datetime.datetime.now()
print('Fecha:' + today_date.strftime("%Y%m%d"))
print('----------------------------------------------------------------')
print('SCRIPT DE DIVISION DE EXCEL')
print('----------------------------------------------------------------')
print('Obteniendo listas')
print('----------------------------------------------------------------')

# Número total de iteraciones
total_iterations = 100

# Crea un objeto tqdm
progress_bar = tqdm(total=total_iterations, desc="Procesando")

# Simula un proceso largo
for i in range(total_iterations):
    # Realiza una tarea
    time.sleep(0.1)  # Simula una operación demorada
    # Actualiza la barra de progreso
    progress_bar.update(1)

# Cierra la barra de progreso
progress_bar.close()

print("Proceso completo")
