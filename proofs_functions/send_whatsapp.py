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
import pywhatkit

print('----------------------------------------------------------------')
print('Bienvenido al proceso para creación de notas de crédito')
dir_path = os.path.dirname(os.path.realpath(__file__))
today_date = datetime.datetime.now()
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
print('----------------------------------------------------------------')

def send_msg():
    pywhatkit.sendwhatmsg_instantly("+525545742835", "olis", True, 2)

    print(f"Se envío el mensaje correctamente")


if __name__ == "__main__":
    send_msg()