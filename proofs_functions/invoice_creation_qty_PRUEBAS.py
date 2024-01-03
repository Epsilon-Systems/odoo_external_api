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

print('----------------------------------------------------------------')
print('Bienvenido al proceso de facturación Walmart')
today_date = datetime.datetime.now()
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#API Configuration
dir_path = os.path.dirname(os.path.realpath(__file__))

#server_url  ='https://wonderbrands.odoo.com'
#db_name = 'wonderbrands-main-4539884'
#username = 'admin'
#password = '9Lh5Z0x*bCqV'

#server_url  ='https://wonderbrands-vobitest-9523648.dev.odoo.com'
#db_name = 'wonderbrands-vobitest-9523648'
#username = 'admin'
#password = '9Lh5Z0x*bCqV'

print('----------------------------------------------------------------')
print('SCRIPT DE CREACIÓN DE FACTURAS POR ITEM')
print('----------------------------------------------------------------')
print('Conectando API Odoo')
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
uid = common.authenticate(db_name, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
print(common)
print('Conexión con Odoo establecida')
print('----------------------------------------------------------------')
print('Conectando a Mysql')
print('----------------------------------------------------------------')
# Connect to MySQL database
mydb = mysql.connector.connect(
  host="wonderbrands1.cuwd36ifbz5t.us-east-1.rds.amazonaws.com",
  user="anibal",
  password="Tuy0TEZOcXAwBgtb",
  database="tech"
)
mycursor = mydb.cursor()
print(f"Leyendo query")
print('Este proceso tomará algo de tiempo, le recomendamos ir por un café')
print('----------------------------------------------------------------')
mycursor.execute("""select b.display_name, a.uuid, a.fecha
                    from finance.sr_sat_emitidas a
                    left join somos_reyes.odoo_new_sale_order b
                        on a.folio = b.channel_order_reference
                    where a.folio in
                        (427233801966,427234601400,430234101900,435233700088,435234600424,436233700325,436234401476,437234501606,438232400331,438234202147,440232501417,440233900936,441234000953,441234100957,767236401365,781235100333,785236600759,789234900560,796236200694,799237001257,801236701108,803236701630,804236701292,805234800510,805234800819,806236500236,807234801455,808234800035,808234900334,809235201713)
                    group by a.uuid
                    order by a.fecha""")
sales_order_records = mycursor.fetchall()
xml_dict = {}
xml_list = []
inv_list = []
sales_error_state = []
sales_no_exist = []
sales_w_inv = []
sales_no_xml = []
sales_mod = []
inv_names = []
inv_ids = []
date_year = '20'
for row in sales_order_records:
    so_name = row[0] #Del query obtiene el nombre de la SO
    xml_name = row[1] #Del query obtiene el nombre del XML o UUID
    xml_date = date_year + row[2].strftime("%y-%m-%d %H:%M:%S") #Del query obtiene también la fecha de la factura

    if so_name not in xml_dict:
        xml_dict[so_name] = [] #si una SO está repetida le agrega multiples xml y fechas correspondientes

    xml_dict[so_name].append(xml_name) #agrega el nombre del xml a una tabla
    xml_dict[so_name].append(xml_date) #agrega la fecha de factura a una tabla

for so_order, xml_files in xml_dict.items():
    value_position = 0
    value_position_date = 1
    so_domain = ['name', '=', so_order]
    for xml_ids in so_order[1]:
        xml_list.append(xml_ids)
    #busca la orden de venta y obtiene el nombre y el estado de SO
    sale_ids = models.execute_kw(db_name, uid, password,'sale.order', 'search_read', [[so_domain]])
    order_name = sale_ids[0]['name']
    order_state = sale_ids[0]['state']
    try:
        #Si existe una orden de venta
        if sale_ids:
            #Si la orden está en Done o bloqueada
            if order_state == 'done':
                invoice_count = sale_ids[0]['invoice_count']
                #Si la cantidad de facturas es menor a 1, ya que si tiene más podría presentar un retorno
                if invoice_count < 1:
                    #Crea una factura para cada orden y para cada item
                    #Obtiene los datos necesarios directo de la SO
                    sale_id = int(sale_ids[0]['id'])
                    currency_id = sale_ids[0]['currency_id'][0]
                    narration = sale_ids[0]['note']
                    campaign_id = False
                    medium_id = sale_ids[0]['medium_id']
                    source_id = sale_ids[0]['source_id']
                    user_id = sale_ids[0]['user_id'][0]
                    invoice_user_id = sale_ids[0]['user_id'][0]
                    team_id = sale_ids[0]['team_id'][0]
                    partner_id = sale_ids[0]['partner_id'][0]
                    partner_shipping_id = sale_ids[0]['partner_shipping_id'][0]
                    fiscal_position_id = sale_ids[0]['fiscal_position_id']
                    partner_bank_id = 1
                    journal_id = 1
                    invoice_origin = sale_ids[0]['name']
                    invoice_payment_term_id = sale_ids[0]['payment_term_id']
                    payment_reference = sale_ids[0]['reference']
                    transaction_ids = sale_ids[0]['transaction_ids']
                    company_id = 1
                    sale_order_line_id = sale_ids[0]['order_line']
                    #sale_order_line_change =  sale_ids[0]['order_line'][0]
                    #Busca el sale_order_line para obtener los datos
                    sol_domain = ['id', 'in', sale_order_line_id]
                    sale_order_line = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[sol_domain]])
                    for inv_lines in sale_order_line:
                        qty_delivered = round(inv_lines['qty_delivered'])
                        qty_uom = round(inv_lines['product_uom_qty'])
                        #Si al cantidad entregada es diferente de 0
                        if qty_delivered != 0:
                            # Inicia un ciclo para cada item en la columna qty_delivered
                            for qty in range(qty_delivered):
                                invoice = {
                                    'ref': '',
                                    'move_type': 'out_invoice',
                                    'currency_id': currency_id,
                                    'narration': narration,
                                    'campaign_id': campaign_id,
                                    'medium_id': medium_id,
                                    'source_id': source_id,
                                    'user_id': user_id,
                                    'invoice_user_id': invoice_user_id,
                                    'team_id': team_id,
                                    'partner_id': partner_id,
                                    'partner_shipping_id': partner_shipping_id,
                                    'fiscal_position_id': fiscal_position_id,
                                    'partner_bank_id': partner_bank_id,
                                    'journal_id': journal_id,  # company comes from the journal
                                    'invoice_origin': invoice_origin,
                                    'invoice_payment_term_id': invoice_payment_term_id,
                                    'payment_reference': payment_reference,
                                    'transaction_ids': [(6, 0, transaction_ids)],
                                    'invoice_line_ids': [],
                                    'company_id': company_id,
                                }
                                line_id = inv_lines['id']
                                invoice_lines = {'display_type': inv_lines['display_type'],
                                                 'sequence': inv_lines['sequence'],
                                                 'name': inv_lines['name'],
                                                 'product_id': inv_lines['product_id'][0],
                                                 'product_uom_id': inv_lines['product_uom'][0],
                                                 #'quantity': sale_order_line[0]['product_qty'],
                                                 'quantity': 1,
                                                 'discount': inv_lines['discount'],
                                                 'price_unit': inv_lines['price_unit'],
                                                 'tax_ids': [(6, 0, [inv_lines['tax_id'][0]])],
                                                 'analytic_tag_ids': [(6, 0, inv_lines['analytic_tag_ids'])],
                                                 'sale_line_ids': [(4, line_id)],
                                                 }
                                invoice['invoice_line_ids'].append((0, 0, invoice_lines))
                                #Crea la factura con el SKU del line_id
                                create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create', [invoice])
                                #print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                                #Busca la factura para agregar mensaje en el chatter
                                #print(f"Agregando mensaje a la factura")
                                search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', create_inv]]])
                                #agrega el id de la factura creada a una tabla
                                inv_ids.append(create_inv)
                                message = {
                                    'body': 'Esta factura fue creada por el equipo de Tech vía API',
                                    'message_type': 'comment',
                                }
                                write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [create_inv], message)
                                # Busca el UUID relacionada con la factura
                                #si existe un archivo XML
                                if xml_files:
                                    #Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                    file_name = xml_files[value_position] #utliza la posición que asignamos anteriormente
                                    file_date = xml_files[value_position_date] #utliza la posición que asignamos anteriormente
                                    file_name_mayus = file_name.upper() #Pone en mayúsculas el nombre del XML
                                    invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Agosto/' #carpeta en la que se encuentran los xmls
                                    xml_file = file_name + '.xml'
                                    xml_file_path = os.path.join(invoices_folder, xml_file)
                                    with open(xml_file_path, 'rb') as f:
                                        xml_data = f.read()
                                    xml_base64 = base64.b64encode(xml_data).decode('utf-8')
                                    #Define los valores del attachment para agregarl el XML
                                    attachment_data = {
                                        'name': xml_file,
                                        'datas': xml_base64,
                                        'res_model': 'account.move',
                                        'res_id': create_inv,
                                    }
                                    #Busca el id del attachment relacionado a la factura
                                    attachment_ids = models.execute_kw(db_name, uid, password, 'ir.attachment', 'create', [attachment_data])
                                    attachment_id = int(attachment_ids)
                                    values = [{
                                        'move_id': create_inv,
                                        'edi_format_id': 2,
                                        'attachment_id': attachment_id,
                                        'state': 'sent',
                                        'create_uid': 1,
                                        'write_uid': 2,
                                    }]
                                    #Agrega el nombre de la factura a la tabla documentos EDI (solo se ve con debug, conta no la usa)
                                    edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'create', values)
                                    #Valida la factura llamando al botón "Confirmar"
                                    upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                    #Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                    upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                    upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'narration': file_name_mayus}])
                                    # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                    upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_date': file_date}])
                                    upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'invoice_payment_term_id': 1}])
                                    #Busca el nombre de la factura una vez publicada meramente infomativo
                                    search_inv_name = models.execute_kw(db_name, uid, password, 'account.move','search_read', [[['id', '=', create_inv]]])
                                    inv_name = search_inv_name[0]['name']
                                    # Busca los asientos de diario relacionados a la factura
                                    #account_line_ids = models.execute_kw(db_name, uid, password, 'account.move.line','search_read', [[['move_id', '=', inv_name]]])
                                    #for each in account_line_ids:
                                    #    move_id = each['id']
                                    #    name_move_id = each['account_id'][1]
                                    #    if name_move_id == '107.05.01 Mercancías Enviadas - No Facturas' or name_move_id == '501-001-001 COSTO DE VENTA':
                                    #        # change_journal_date = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date': inv_date}])
                                    #        change_journal_mat = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id],{'date_maturity': file_date}])
                                    #    else:
                                    #        change_journal_date = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id], {'date': file_date}])
                                    #        change_journal_mat = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id],{'date_maturity': file_date}])
                                    #    print(f"Nombre del Apunte de diario: {name_move_id}")
                                    #posiciones de los array
                                    value_position += 2
                                    value_position_date += 2
                                    sales_mod.append(order_name) #agrega el nombre de la orden a otra tabla
                                    inv_names.append(inv_name) #agrega el nombre que se le asignó a la factura
                                    #print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                else:
                                    print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                    sales_no_xml.append(order_name)
                                    continue
                        else:
                            print("Se encontró una factura con cantidad entregada en 0, se tomará en cuenta solo la cantidad")
                            #Inicia un ciclo para cada item en la columna qty_uom
                            for qty in range(qty_uom):
                                invoice = {
                                    'ref': '',
                                    'move_type': 'out_invoice',
                                    'currency_id': currency_id,
                                    'narration': narration,
                                    'campaign_id': campaign_id,
                                    'medium_id': medium_id,
                                    'source_id': source_id,
                                    'user_id': user_id,
                                    'invoice_user_id': invoice_user_id,
                                    'team_id': team_id,
                                    'partner_id': partner_id,
                                    'partner_shipping_id': partner_shipping_id,
                                    'fiscal_position_id': fiscal_position_id,
                                    'partner_bank_id': partner_bank_id,
                                    'journal_id': journal_id,  # company comes from the journal
                                    'invoice_origin': invoice_origin,
                                    'invoice_payment_term_id': invoice_payment_term_id,
                                    'payment_reference': payment_reference,
                                    'transaction_ids': [(6, 0, transaction_ids)],
                                    'invoice_line_ids': [],
                                    'company_id': company_id,
                                }
                                # line_id = sale_order_line[0]['id']
                                line_id = inv_lines['id']
                                invoice_lines = {'display_type': inv_lines['display_type'],
                                                 'sequence': inv_lines['sequence'],
                                                 'name': inv_lines['name'],
                                                 'product_id': inv_lines['product_id'][0],
                                                 'product_uom_id': inv_lines['product_uom'][0],
                                                 # 'quantity': sale_order_line[0]['product_qty'],
                                                 'quantity': 1,
                                                 'discount': inv_lines['discount'],
                                                 'price_unit': inv_lines['price_unit'],
                                                 'tax_ids': [(6, 0, [inv_lines['tax_id'][0]])],
                                                 'analytic_tag_ids': [(6, 0, inv_lines['analytic_tag_ids'])],
                                                 'sale_line_ids': [(4, line_id)],
                                                 }
                                invoice['invoice_line_ids'].append((0, 0, invoice_lines))
                                create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create',
                                                               [invoice])
                                # Busca la factura para agregar mensaje en el chatter
                                search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',
                                                               [[['id', '=', create_inv]]])
                                message = {
                                    'body': 'Esta factura fue creada por el equipo de Tech vía API',
                                    'message_type': 'comment',
                                }
                                write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move',
                                                                  'message_post', [create_inv], message)
                                # Busca si hay un UUID relacionada con la factura
                                if xml_files:
                                    # Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                    file_name = xml_files[value_position]
                                    file_date = xml_files[value_position_date]
                                    file_name_mayus = file_name.upper()
                                    invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Agosto/'
                                    xml_file = file_name + '.xml'
                                    xml_file_path = os.path.join(invoices_folder, xml_file)
                                    with open(xml_file_path, 'rb') as f:
                                        xml_data = f.read()
                                    xml_base64 = base64.b64encode(xml_data).decode('utf-8')
                                    # Define los valores del attachment para agregarl el XML
                                    attachment_data = {
                                        'name': xml_file,
                                        'datas': xml_base64,
                                        'res_model': 'account.move',
                                        'res_id': create_inv,
                                    }
                                    # Busca el id del attachment relacionado a la factura
                                    attachment_ids = models.execute_kw(db_name, uid, password, 'ir.attachment',
                                                                       'create', [attachment_data])
                                    attachment_id = int(attachment_ids)
                                    values = [{
                                        'move_id': create_inv,
                                        'edi_format_id': 2,
                                        'attachment_id': attachment_id,
                                        'state': 'sent',
                                        'create_uid': 1,
                                        'write_uid': 2,
                                    }]
                                    # Agrega el nombre de la factura a la tabla documentos EDI (solo se ve con debug, conta no la usa)
                                    edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','create', values)
                                    # Valida la factura llamando al botón "Confirmar"
                                    upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                    # Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                    upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                    upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'narration': file_name_mayus}])
                                    # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                    upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_date': file_date}])
                                    upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'invoice_payment_term_id': 1}])
                                    # Busca el nombre de la factura una vez publicada meramente infomativo
                                    search_inv_name = models.execute_kw(db_name, uid, password, 'account.move','search_read', [[['id', '=', create_inv]]])
                                    inv_name = search_inv_name[0]['name']
                                    # Busca los asientos de diario relacionados a la factura
                                    #account_line_ids = models.execute_kw(db_name, uid, password, 'account.move.line','search_read', [[['move_id', '=', inv_name]]])
                                    #for each in account_line_ids:
                                    #    move_id = each['id']
                                    #    name_move_id = each['account_id'][1]
                                    #    if name_move_id == '107.05.01 Mercancías Enviadas - No Facturas' or name_move_id == '501-001-001 COSTO DE VENTA':
                                    #        # change_journal_date = models.execute_kw(db_name, uid, password, 'account.move.line', 'write',[[move_id], {'date': inv_date}])
                                    #        change_journal_mat = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id],{'date_maturity': file_date}])
                                    #    else:
                                    #        change_journal_date = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id], {'date': file_date}])
                                    #        change_journal_mat = models.execute_kw(db_name, uid, password,'account.move.line', 'write',[[move_id],{'date_maturity': file_date}])
                                    #    print(f"Nombre del Apunte de diario: {name_move_id}")
                                    # posiciones de los array
                                    value_position += 2
                                    value_position_date += 2
                                    sales_mod.append(order_name)
                                    inv_names.append(inv_name)
                                    # print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                else:
                                    print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                    continue
                else:
                    print(f'La orden de venta: {order_name} ya tiene una factura creada')
                    print('----------------------------------------------------------------')
                    sales_w_inv.append(order_name)
                    continue
            else:
                print(f"Revise el estatus de la orden {order_name} se encuentra en estatus {order_state}")
                print(f"Por lo que esta orden no puede ser facturada")
                sales_error_state.append(order_name)
                continue
        else:
            print(f'El ID de la orden: {order_name} no coincide con ninguna venta en Odoo')
            sales_no_exist.append(order_name)
            continue
    except Exception as e:
        print(f"Error al crear la factura de la orden {order_name}: {e}")

print('Definiendo correo para contabilidad')
msg = MIMEMultipart()
body = '''\
<html>
  <head></head>
  <body>
    <p>Buenas tardes</p>
    <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de autofacturación Walmart.</p>
    <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales se les creó una factura, órdenes que no se pudieron facturar, nombre de las facturas creadas y su ids correspondientes.</p>
    </br>
    <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
    </br>
    <p>Muchas gracias</p>
    </br>
    <p>Un abrazo</p>
  </body>
</html>
'''
print('Creando archivo Excel')
print('----------------------------------------------------------------')
# Crear el archivo Excel y agregar los nombres de los arrays y los resultados
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet['A1'] = 'sales_error_state'
sheet['B1'] = 'sales_no_exist'
sheet['C1'] = 'sales_w_inv'
sheet['D1'] = 'sales_no_xml'
sheet['E1'] = 'sales_mod'
sheet['F1'] = 'inv_names'
sheet['G1'] = 'inv_ids'
# Agregar los resultados de los arrays
for i in range(len(sales_error_state)):
    sheet['A{}'.format(i+2)] = sales_error_state[i]
for i in range(len(sales_no_exist)):
    sheet['B{}'.format(i+2)] = sales_no_exist[i]
for i in range(len(sales_w_inv)):
    sheet['C{}'.format(i+2)] = sales_w_inv[i]
for i in range(len(sales_no_xml)):
    sheet['D{}'.format(i+2)] = sales_no_xml[i]
for i in range(len(sales_mod)):
    sheet['E{}'.format(i+2)] = sales_mod[i]
for i in range(len(inv_names)):
    sheet['F{}'.format(i+2)] = inv_names[i]
for i in range(len(inv_ids)):
    sheet['G{}'.format(i+2)] = inv_ids[i]
# Guardar el archivo Excel en disco
excel_file = 'balance_general_' + today_date.strftime("%Y%m%d") + '.xlsx'
workbook.save(excel_file)
# Leer el contenido del archivo Excel
with open(excel_file, 'rb') as file:
    file_data = file.read()
file_data_encoded = base64.b64encode(file_data).decode('utf-8')
#Define el encabezado y las direcciones del remitente y destinatarios
print('Definiendo remitente y destinatarios')
print('----------------------------------------------------------------')
msg = MIMEMultipart()
msg['From'] = 'Tech anibal@wonderbrands.co'
msg['To'] = ', '.join(['anibal@wonderbrands.co','rosalba@wonderbrands.co','natalia@wonderbrands.co','greta@somos-reyes.com','contabilidad@somos-reyes.com','alex@wonderbrands.co','will@wonderbrands.co'])
msg['Subject'] = 'Cierre de facturación - Walmart'
# Adjuntar el cuerpo del correo
msg.attach(MIMEText(body, 'html'))
# Adjuntar el archivo Excel al mensaje
attachment = MIMEBase('application', 'octet-stream')
attachment.set_payload(file_data)
encoders.encode_base64(attachment)
attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
msg.attach(attachment)

#Define variables del servidor de correo
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'anibal@wonderbrands.co'
smtp_password = 'iwvrlrxkiydxueer'
print('Enviando correo con listas de ordenes y facturas')
print('----------------------------------------------------------------')
try:
   smtpObj = smtplib.SMTP(smtp_server, smtp_port)
   smtpObj.starttls()
   smtpObj.login(smtp_username, smtp_password)
   smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
   print("Correo enviado correctamente")
except Exception as e:
   print(f"Error: no se pudo enviar el correo: {e}")

print(f"Ordenes que no están en done {sales_error_state}")
print(f"Ordenes que no existen en Odoo {sales_no_exist}")
print(f"Ordenes que ya tenían una factura {sales_w_inv}")
print(f"Ordenes sin XML {sales_no_xml}")
print(f"Ordenes a las que se les creo factura: {sales_mod}")
print(f"Nombre de las facturas creadas: {inv_names}")
print(f"IDs de las facturas creadas: {inv_ids}")

mycursor.close()
mydb.close()
smtpObj.quit()
