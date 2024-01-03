import time

from flask import Flask, render_template, request, make_response, url_for, session
from os import listdir
from os.path import isfile, join
from datetime import date, datetime, timedelta
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
password = 'nK738*rxc#nd'

#server_url  ='https://wonderbrands-v3-8917917.dev.odoo.com'
#db_name = 'wonderbrands-v3-8917917'
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
mycursor.execute("""select b.order_id, a.uuid, a.fecha
                    from finance.sr_sat_emitidas a
                    left join somos_reyes.odoo_master_txns_c b
                        on a.folio = b.marketplace_order_id
                    where a.folio in
                        (706236801889,706236801889,706236801889,350234103532,350232706094,339234000545,694235200239,715235308804,706236801889,350234402976,706236801889,706236801889,712236503465,345234201581,716236601929,706236801889,712236503034,715236400877,706236801889,706236801889,706236801889,691235312821,706236801889,706236801889,706236801889,350234103532,706236801889,345234201581,706236801889,706236801889,695235001618,706236801889,711236500662,350234103532,706236801889,714236200224,323234200076,332234000420,106490309350,340234600861,323234200076,323234200076,717234901230,332234000420,348234502990,332234000420,349234100101,350233700475,332234000420,710236701729,710236701729,710236701729,700236600311,332233800878,715236400281,106524564497,332233800878,332233800878,332233800878,332233800878,704236500533,338234002367,698236602077,351233700305,342232400833,695236401044,695236401044,696235000052,695236401044,696235000052,350233901428,695236401044,708237101484,350232401652,350232401652,350232401652,350232401652,344234101499,350232401652,712235300429,351234001022,715236802797,347234203330,716235004039,347233801069,347233801069,712236804067,712236804067,346234505915,346234505915,346234505915,712236804067,717236200828,715236803920,715236803920,712235109330,713236200823,712235109330,708237100937,106280417396,716235300916)
                    group by a.uuid
                    order by b.order_id""")
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
    so_name = row[0]
    xml_name = row[1]
    xml_date = date_year + row[2].strftime("%y-%m-%d %H:%M:%S")

    if so_name not in xml_dict:
        xml_dict[so_name] = []

    xml_dict[so_name].append(xml_name)
    xml_dict[so_name].append(xml_date)
for so_order, xml_files in xml_dict.items():
    value_position = 0
    value_position_date = 1
    so_domain = ['name', '=', so_order]
    for xml_ids in so_order[1]:
        xml_list.append(xml_ids)
    sale_ids = models.execute_kw(db_name, uid, password,'sale.order', 'search_read', [[so_domain]])
    order_name = sale_ids[0]['name']
    order_state = sale_ids[0]['state']
    print(f"Orden de venta encontrada en el sistema")
    try:
        if order_state == 'done':
            if sale_ids:
                invoice_count = sale_ids[0]['invoice_count']
                #if invoice_count < 1:
                # Create invoice for sales order
                sale_id = int(sale_ids[0]['id'])
                #for sale_order in sale_ids:
                #sale_id = int(sale_order['id'])
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
                # Call to sale order line to get order line data
                sol_domain = ['id', 'in', sale_order_line_id]
                sale_order_line = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[sol_domain]])
                for inv_lines in sale_order_line:
                    qty_delivered = round(inv_lines['qty_delivered'])
                    qty_uom = round(inv_lines['product_uom_qty'])
                    if qty_delivered != 0:
                        for qty in range(qty_delivered):
                            print("DATOS DE FACTURA")
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
                            #line_id = sale_order_line[0]['id']
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
                            create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create', [invoice])
                            print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                            #Busca la factura para agregar mensaje en el chatter
                            print(f"Agregando mensaje a la factura")
                            search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', create_inv]]])
                            inv_ids.append(create_inv)
                            message = {
                                'body': 'Esta factura fue creada por el equipo de Tech vía API',
                                'message_type': 'comment',
                            }
                            write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [create_inv], message)
                            # Busca el UUID relacionada con la factura
                            if xml_files:
                                #Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                file_name = xml_files[value_position]
                                file_date = xml_files[value_position_date]
                                file_name_mayus = file_name.upper()
                                print(f"AGREGANDO ARCHIVO XML A LA FACTURA")
                                invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Junio/'
                                print(f"El xml {file_name} será agregado a la factura")
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
                                print('AGREGANDO REGISTRO XML A LA TABLA DOCUMENTOS EDI')
                                edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'create', values)
                                print('Registro account.edi.document creado')
                                #Valida la factura llamando al botón "Confirmar"
                                upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                print('Se publica la factura: ', create_inv)
                                #Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                print(f"Se agrega el folio fiscal: {file_name_mayus}")
                                upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'narration': file_name_mayus}])
                                # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                print(f"Se Modifica la fecha de factura: {file_date}")
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
                                sales_mod.append(order_name)
                                inv_names.append(inv_name)
                                #print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                print('-------------------------------------------------------')
                            else:
                                print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                sales_no_xml.append(order_name)
                                continue
                    else:
                        print(f"La cantidad entregada es igual a {qty_delivered}")
                        print(f"Se tomará en cuenta el campo qty_uom")
                        for qty in range(qty_uom):
                            print("DATOS DE FACTURA")
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
                            print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                            # Busca la factura para agregar mensaje en el chatter
                            print(f"Agregando mensaje a la factura")
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
                                print(f"AGREGANDO ARCHIVO XML A LA FACTURA")
                                invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Junio/'
                                print(f"El xml {file_name} será agregado a la factura")
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
                                print('AGREGANDO REGISTRO XML A LA TABLA DOCUMENTOS EDI')
                                edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','create', values)
                                print('Registro account.edi.document creado')
                                # Valida la factura llamando al botón "Confirmar"
                                upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                print('Se publica la factura: ', create_inv)
                                # Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                print(f"Se agrega el folio fiscal: {file_name_mayus}")
                                upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'narration': file_name_mayus}])
                                # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                print(f"Se Modifica la fecha de factura: {file_date}")
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
                                print('-------------------------------------------------------')
                            else:
                                print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                continue
                #HOOLA
                #else:
                #    print(f'La orden de venta: {order_name} ya tiene una factura creada')
                #    print('----------------------------------------------------------------')
                #    sales_w_inv.append(order_name)
                #    continue
            else:
                print(f'El ID de la orden: {order_name} no coincide con ninguna venta en Odoo')
                sales_no_exist.append(order_name)
                continue
        else:
            print(f"Revise el estatus de la orden {order_name} se encuentra en estatus {order_state}")
            print(f"Por lo que esta orden no puede ser facturada")
            sales_error_state.append(order_name)
            continue
    except Exception as e:
        print(f"Error al crear la factura de la orden {order_name}: {e}")

print(f"Ordenes que no están en done {sales_error_state}")
print(f"Ordenes que no existen en Odoo {sales_no_exist}")
print(f"Ordenes que ya tenían una factura {sales_w_inv}")
print(f"Ordenes sin XML {sales_no_xml}")
print(f"Ordenes a las que se les creo factura: {sales_mod}")
print(f"Nombre de las facturas creadas: {inv_names}")
print(f"IDs de las facturas creadas: {inv_ids}")

mycursor.close()
mydb.close()
