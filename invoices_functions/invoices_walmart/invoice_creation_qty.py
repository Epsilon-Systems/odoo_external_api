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

print('================================================================')
print('BIENVENIDO AL PROCESO DE FACTURACIÓN WALMART')
print('================================================================')
print('SCRIPT DE CREACIÓN DE FACTURAS POR ITEM')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'C:\Dev\wb_odoo_external_api\config\config.json'

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
def invoice_create_qty():
    # Obtener credenciales
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
    print('Este proceso tomará algo de tiempo, le recomendamos ir por un café')
    print('----------------------------------------------------------------')
    mycursor.execute("""select b.name, a.uuid, a.fecha
                        from finance.sr_sat_emitidas a
                        left join somos_reyes.odoo_new_sale_order b
                        on a.folio = b.channel_order_reference
                        WHERE extract(year_month from a.fecha) = 202312
                            and b.channel like '%walmart%' 
                            and b.team_name like '%walmart%'
                            and b.state not in ('draft','sent','cancel')
                            and a.folio in (522234102207,528234500306,894236000482,528234401283,528234400777,528234500686,894237000880,529232801285,529233100144,530232501717,529234200037,897236601213,531234401387,531234501544,531234600964,531234600048,898234801675,532232600485,532232700002,532234200497,532234200971,532234401100,532234600449,886236501823,887236203523,899236601136,533234300114,533234202277,533234400217,897237001595,899236900914,533234600288,533234601415,533234601430,533234601403,533234701064,900234801845,900235001722,477232701066,534233900585,900236300695,900236500346,534234001164,899236600972,532234201668,457234400056,900236600035,534234102018,900236502455,534234301006,900236601582,534234501862,900237001028,900237000371,534234601779,901235900031,901236100534,535234100812,535234101601,535234201083,532234700036,901236800237,898236700314,535234401763,535234600915,535234601509,890235200653,902236502055,903234800025,903234900504,537232400096,903236701404,537234601871,536232601728,904236600642,538234400547,538234505897,538234702717,539232700334,539232701837,905235300830,905236200749,539234001517,905236502101,905236800154,539234401438,540232400764,535232602582,537232700346,906234901189,540232800805,906235400197,540233700134,540233902066,906236700333,906236401510,906236904618,906236904604,906236904527,906236903843,540234603654,906237101281,907234802000,541232600807,541233900361,541234001568,540234600204,541234102025,541234200582,540233900862,907236900981,907236901060,541234101926,908234901890,908236201224,541233400246,541234302691,542234100568,908236600129,901235900248,907237100317,542234001968,908236401882,907235101900,542234700173,542234700182,908237100906,882235402053,909234901372,909235200483,543233900842,543234302459,543233000433,867234900084,910236602412,910237000984,544234700488,545232500769,545232602184,911235101471,528234301105,911235300956,911235401016,545233801266,891235202589,545234301948,911236801745,545234502458,545234501666,541232401595,911237003060,545234700870,546232402736,546234105704,546234105980,546234106196,912236506745,912236700863,546234401521,547232401169,891234807622,912237102528,547232600967,913235100685,913235101739,888235005320,547234701714,548232401320,547233700826,548233900573,914236600771,914236600612,914236800210,548234400296,548234300202,548234700880,915234801819,915236501374,549234103206,549234301094,915237102368,916234902069,859234900449,550234601181,522232405321,917235400683,917235400369,917236600811,551234302145,917236701186,917237100467,918235002040,916235500540,912236303076,552234201059,911234900333,844235101246,519234001515,853237000243,553233900760,919236201379,552233901345,553234000078,510234002159,553234200000,553234403090,553234601860,920236000037,554234102568,921235100055,555234300108,921236900743,921237000102,555234701834,921237101959,920237101945,556232602307,556232900456,889236200900,531234601746,556234100735,556234400159,923235001206,558234100038,924237100527,558234600479,925236400781)
                        group by a.uuid
                        order by a.fecha
                        """)
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

    progress_bar = tqdm(total=len(sales_order_records), desc="Procesando")
    for so_order, xml_files in xml_dict.items():
        value_position = 0
        value_position_date = 1
        so_domain = ['name', '=', so_order]
        for xml_ids in so_order[1]:
            xml_list.append(xml_ids)
        #busca la orden de venta y obtiene el nombre y el estado de SO
        sale_ids = models.execute_kw(db_name, uid, password,'sale.order', 'search_read', [[so_domain]])
        try:
            #Si existe una orden de venta
            if sale_ids:
                order_name = sale_ids[0]['name']
                order_state = sale_ids[0]['state']
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
                                        invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/diciembre/' #carpeta en la que se encuentran los xmls
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
                                        int_id = search_inv_name[0]['id']
                                        inv_name = search_inv_name[0]['name']
                                        inv_edi_state = search_inv_name[0]['edi_state']

                                        #UPDATE Diciembre-2023
                                        attachment = models.execute_kw(db_name, uid, password, 'ir.attachment', 'search_read',[[['res_id', '=', create_inv]]])[0]
                                        edi_document_fix = models.execute_kw(db_name, uid, password, 'account.edi.document','search_read', [[['move_id', '=', create_inv]]])

                                        if inv_edi_state != 'sent':
                                            if attachment:
                                                att_id = attachment['id']
                                                for edi in edi_document_fix:
                                                    edi_id = edi['id']  # ID del registro en la tabla EDI
                                                    edi_name = edi['edi_format_name']  # Nombre del registro en la tabla EDI
                                                    edi_state = edi['state']  # Estado del registro en la tabla EDI
                                                    if edi_name == 'CFDI (3.3)':
                                                        # Elimina el registro de la tabla EDI.DOCUMENT
                                                        del_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','unlink', [[edi_id]])
                                                        # Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                                        values = [{
                                                            'move_id': int_id,
                                                            'edi_format_id': 2,
                                                            'attachment_id': att_id,
                                                            'state': 'sent',
                                                            'create_uid': 1,
                                                            'write_uid': 2,
                                                        }]
                                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                                        new_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','create', values)
                                                    else:
                                                        continue
                                            else:
                                                print(f'La orden: {order_name} no tiene un XML adjunto')
                                                continue
                                        else:
                                            print(f'La orden: {order_name} no está en estado "Por enviar"')
                                            continue

                                        #posiciones de los array
                                        value_position += 2
                                        value_position_date += 2
                                        sales_mod.append(order_name) #agrega el nombre de la orden a otra tabla
                                        inv_names.append(inv_name) #agrega el nombre que se le asignó a la factura
                                        progress_bar.update(1)
                                        #print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    else:
                                        print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                        sales_no_xml.append(order_name)
                                        progress_bar.update(1)
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
                                        invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/diciembre/'
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
                                        int_id = search_inv_name[0]['id']
                                        inv_name = search_inv_name[0]['name']
                                        inv_edi_state = search_inv_name[0]['edi_state']

                                        # UPDATE Diciembre-2023
                                        attachment = models.execute_kw(db_name, uid, password, 'ir.attachment', 'search_read',[[['res_id', '=', create_inv]]])[0]
                                        edi_document_fix = models.execute_kw(db_name, uid, password,'account.edi.document', 'search_read',[[['move_id', '=', create_inv]]])

                                        if inv_edi_state != 'sent':
                                            if attachment:
                                                att_id = attachment['id']
                                                for edi in edi_document_fix:
                                                    edi_id = edi['id']  # ID del registro en la tabla EDI
                                                    edi_name = edi['edi_format_name']  # Nombre del registro en la tabla EDI
                                                    edi_state = edi['state']  # Estado del registro en la tabla EDI
                                                    if edi_name == 'CFDI (3.3)':
                                                        # Elimina el registro de la tabla EDI.DOCUMENT
                                                        del_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','unlink', [[edi_id]])
                                                        # Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                                        values = [{
                                                            'move_id': int_id,
                                                            'edi_format_id': 2,
                                                            'attachment_id': att_id,
                                                            'state': 'sent',
                                                            'create_uid': 1,
                                                            'write_uid': 2,
                                                        }]
                                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                                        new_edi_document = models.execute_kw(db_name, uid, password,
                                                                                             'account.edi.document',
                                                                                             'create', values)
                                                    else:
                                                        continue
                                            else:
                                                print(f'La orden: {order_name} no tiene un XML adjunto')
                                                continue
                                        else:
                                            print(f'La orden: {order_name} no está en estado "Por enviar"')
                                            continue
                                        # posiciones de los array
                                        value_position += 2
                                        value_position_date += 2
                                        sales_mod.append(order_name)
                                        inv_names.append(inv_name)
                                        progress_bar.update(1)
                                        # print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    else:
                                        print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                        progress_bar.update(1)
                                        continue
                    else:
                        print(f'La orden de venta: {order_name} ya tiene una factura creada')
                        print('----------------------------------------------------------------')
                        sales_w_inv.append(order_name)
                        progress_bar.update(1)
                        continue
                else:
                    print(f"Revise el estatus de la orden {order_name} se encuentra en estatus {order_state}")
                    print(f"Por lo que esta orden no puede ser facturada")
                    sales_error_state.append(order_name)
                    progress_bar.update(1)
                    continue
            else:
                print(f'El ID de la orden: {order_name} no coincide con ninguna venta en Odoo')
                sales_no_exist.append(order_name)
                progress_bar.update(1)
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
    excel_file = 'ordenes_autofacturadas_' + today_date.strftime("%Y%m%d") + '.xlsx'
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
    msg['Subject'] = 'Cierre de facturación de órdenes autofacturadas - Walmart'
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

    progress_bar.close()
    mycursor.close()
    mydb.close()
    smtpObj.quit()

if __name__ == "__main__":
    invoice_create_qty()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duraciòn del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')